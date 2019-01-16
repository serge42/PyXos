import pickle
import select
import socket
import sys
import time

from threading import Event, Thread

from message import *
from socket_helper import getUDPMulticastSocket as create_socket


flag = Event()
buffer = []


class Proposer(Thread):
    """
    Easy start, process with id 0 is leader/coordinator
    """

    def __init__(self, id, addr, port, acceptors_addr, acceptors_port, clients_addr, clients_port, learners_addr, learners_port):
        Thread.__init__(self)
        self.id = id
        self.proposers = (addr, port)
        self.clients = (clients_addr, clients_port)
        self.acceptors = (acceptors_addr, acceptors_port)
        self.learners = (learners_addr, learners_port)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                         socket.IPPROTO_UDP)  # IP, UDP

        self.active = True
        self.is_leader = True
        self.known_acceptors = []
        self.pending_clients = []
        self.crnt_ballot = 0

    def run(self):
        global buffer

        print('Worker running')
        pending = {}  # ballot_num -> ([acc_ids], value)
        pending2b = {}
        last_msg = None
        resends = 0
        timeout = .1

        try:
            # inform everyone that this is the leader
            self.send_message(
                Message(Indicators.PROPOSERS, (self.id, self.crnt_ballot)), self.proposers)
            while self.active:
                # print(str.format("worker: {0}", len(buffer)))
                flag.wait(timeout)
                if len(pending) <= 0 and len(pending2b) <= 0 and len(self.pending_clients) > 0:
                    msg = self.pending_clients.pop(0)
                elif len(buffer) > 0:
                    msg = buffer.pop(0)
                elif len(pending) > 0 and last_msg != None:
                    # maybe a msg was dropped
                    # print("resends={0}, crnt_ballot={1}".format(resends, self.crnt_ballot))
                    b = last_msg.msg.ballot_num
                    if self.crnt_ballot > b:
                        self.pending_clients = [Message(Indicators.CLIENTS, pending[b][1])] + self.pending_clients
                        pending.pop(b)
                    elif resends <= 5:
                        self.send_message(last_msg, self.acceptors)
                        
                    resends = resends+1
                    continue
                else:
                    continue

                if msg.indicator == Indicators.ACCEPTORS:
                    aid, a_ballot = msg.msg
                    # print("recvd acc {0}, ballot {1}".format(aid, a_ballot))
                    if not aid in self.known_acceptors:
                        self.known_acceptors.append(aid)
                    if self.crnt_ballot <= a_ballot:
                        self.crnt_ballot = a_ballot + 1
                    self.should_wait(len(pending))
                    continue

                if msg.indicator == Indicators.PROPOSERS:
                    pid, p_ballot = msg.msg
                    if pid < self.id:
                        self.is_leader = False
                        print("[{0}] is not leader".format(self.id))
                    if p_ballot > self.crnt_ballot:
                        self.crnt_ballot = p_ballot + 1

                # Assume leader IS known after this point
                if self.is_leader:
                    resends = 0
                    if msg.indicator == Indicators.CLIENTS:  # Msg from client
                        if len(pending) <= 0:
                            print('sending p1a')
                            value = msg.msg
                            self.crnt_ballot = self.crnt_ballot + 1
                            phase = Phase1a(self.id, self.crnt_ballot)
                            last_msg = Message(Indicators.PHASE1A, phase)
                            self.send_message(last_msg, self.acceptors)
                            pending[self.crnt_ballot] = ([], msg.msg)
                        else:
                            self.pending_clients.append(msg)

                    elif msg.indicator == Indicators.PHASE1B:
                        phase1b = msg.msg  # wait for quorum
                        b = phase1b.ballot_num
                        if phase1b.acceptor_id not in self.known_acceptors:
                            self.known_acceptors.append(phase1b.acceptor_id)
                        if b in pending:
                            # increase number of acceptors, keep val
                            acceptor_list = pending[b][0]
                            if not phase1b.acceptor_id in acceptor_list:
                                acceptor_list.append(phase1b.acceptor_id)
                            pending[b] = (acceptor_list, pending[b][1])
                            if phase1b.accepted and b == phase1b.accepted[0]:
                                pending[b] = (
                                    pending[b][0], phase1b.accepted[b])

                            # test if quorum achieved
                            # print("Ballot {0} recvd {1} p1b and waits for {2}".format(b, pending[b][0], (len(self.known_acceptors)+1)//2))
                            if len(pending[b][0]) > len(self.known_acceptors)/2:
                                phase2a = Phase2a(
                                    self.crnt_ballot, pending[b][1])
                                last_msg = Message(Indicators.PHASE2A, phase2a)
                                self.send_message(last_msg, self.acceptors)
                                pending2b[b] = ([], pending[b][1])
                        else:
                            print(
                                "[{0}] Ballot {1} not in pending".format(self.id, b))

                    elif msg.indicator == Indicators.PHASE2B:
                        phase2b = msg.msg
                        b = phase2b.ballot_num
                        if phase2b.acceptor_id not in self.known_acceptors:
                            self.known_acceptors.append(phase2b.acceptor_id)
                        if b in pending2b:
                            acceptor_list = pending2b[b][0]
                            if not phase2b.acceptor_id in acceptor_list:
                                acceptor_list.append(phase2b.acceptor_id)
                            pending2b[b] = (acceptor_list, pending2b[b][1])
                            print("[{0}] Pending2b: {1}".format(
                                self.id, pending2b[b][0]))
                            if len(pending2b[b][0]) > len(self.known_acceptors)/2:
                                print("[{0}] Ballot {1}: accepted val=[{2}]".format(
                                    self.id, b, pending2b[b][1]))
                                # learners_msg = Message(Indicators.PROPOSERS, Result(b, pending[b][1]))
                                # self.send_message(learners_msg, self.learners)
                                pending.pop(b)
                                pending2b.pop(b)
                                last_msg = None
                else:
                    # print("[{0}] not leader".format(self.id))
                    # TODO: elect new leader if necessary -> heartbeat protocol
                    pass

                self.should_wait(len(pending))
            # end while
        except Exception as e:
            print("{0} exception: {1}".format(type(e), e))

    def send_message(self, msg, dest):
        self.send_socket.sendto(pickle.dumps(msg), dest)

    def should_wait(self, pendings):
        if len(buffer) <= 0 and (len(self.pending_clients) <= 0 or pendings > 0):
            flag.clear()

    def quit(self):
        self.active = False


class Listener(Thread):
    def __init__(self, address, port):
        Thread.__init__(self)
        self.address = (address, port)
        self.active = True
        self.s = None

    def run(self):
        global buffer

        print('Listener running')
        # Listen to acceptors
        self.s = create_socket(self.address)
        self.s.setblocking(False)
        timeout = .1  # seconds
        try:
            while self.active:
                    # in case a message is sent in multiple packets
                ready = select.select([self.s], [], [], timeout)
                if not ready[0]:
                    continue
                    
                data = self.s.recv(1024)
                try:
                    msg = pickle.loads(data)
                    # print("Got a {0} message".format(msg.indicator.name))
                    buffer.append(msg)
                    flag.set()
                except pickle.UnpicklingError as upe:
                    # not sure why this happens, try closing socket and creating a new one
                    print(upe)
                    self.s.close()
                    self.s = create_socket(self.address)
                except Exception as e:
                    print("{0}: {1}".format(type(e), e))
            self.s.close()
        except Exception as e:
            print("[listener] {0} exception: {1}".format(type(e), e))
            self.s.close()
            exit(103)

    def quit(self):
        self.active = False


if __name__ == '__main__':
    if len(sys.argv) == 10:
        id = int(sys.argv[1])
        addr = sys.argv[2]
        port = int(sys.argv[3])

        listener = Listener(addr, port)
        p = Proposer(id, addr, port, sys.argv[4], int(sys.argv[5]), sys.argv[6], int(
            sys.argv[7]), sys.argv[8], int(sys.argv[9]))

        try:
            listener.start()
            p.start()

            listener.join()
            p.join()
        except KeyboardInterrupt:
            print('quitting...')
            p.quit()
            listener.quit()
    else:
        print("Usage: ..." + len(sys.argv))
