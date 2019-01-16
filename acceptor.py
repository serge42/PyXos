import pickle
import select
import socket
import sys
import time

from message import *
from socket_helper import getUDPMulticastSocket as create_socket


class Acceptor:
    """
    """

    def __init__(self, id, acceptors_addr, acceptors_port, proposers_addr, proposers_port, learners_addr, learners_port):
        self.id = id
        self.listen_addr = (acceptors_addr, acceptors_port)
        self.port = acceptors_port
        self.proposers = (proposers_addr, proposers_port)
        self.learners = (learners_addr, learners_port)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                         socket.IPPROTO_UDP)  # IP, UDP

        self.active = True
        self.s = create_socket(self.listen_addr)
        self.ballot_num = -1

    def start(self):
        msg = Message(Indicators.ACCEPTORS, (self.id, self.ballot_num))
        self.send_message(msg, self.proposers)
        self.run()

    def run(self):
        print('Acceptor {0} running'.format(self.id))
        # Listen to acceptors
        accepted = {}
        timeout = .1 # seconds
        try:
            while self.active:
                ready = select.select([self.s], [], [], timeout)
                if not ready:
                    continue

                data, addr = self.s.recvfrom(4096)  # buffer size
                msg = pickle.loads(data)

                if msg.indicator == Indicators.PHASE1A:
                    phase1a = msg.msg
                    b = phase1a.ballot_num
                    print("[{0}]> p1a: {1} {2}".format(self.id, b, addr))
                    if self.ballot_num < b:  # accept phase 1
                        last_accepted = None
                        if self.ballot_num in accepted:
                            last_accepted = (self.ballot_num, accepted[self.ballot_num])
                        self.ballot_num = b
                        phase1b = Phase1b(b=b, aid=self.id, accepted=last_accepted)
                        self.send_message(
                            Message(Indicators.PHASE1B, phase1b), self.proposers)
                    else:
                        self.send_message(Message(Indicators.ACCEPTORS, (self.id, self.ballot_num)), self.proposers)

                elif msg.indicator == Indicators.PHASE2A:
                    phase2a = msg.msg
                    b = phase2a.ballot_num
                    print("[{0}]> p2a: {1}(val={3}) {2}".format(self.id, b, addr, phase2a.value))
                    if b == self.ballot_num:
                        accepted[b] = phase2a.value
                    phase2b = Phase2b(b, self.id, phase2a.value)
                    # time.sleep(10)
                    accept_msg = Message(Indicators.PHASE2B, phase2b)
                    self.send_message(accept_msg, self.proposers)
                    self.send_message(accept_msg, self.learners)
            self.s.close()
        except Exception as e:
            print(e)
            self.s.close()

    def send_message(self, msg, dest):
        self.send_socket.sendto(pickle.dumps(msg), dest)
        print(str.format("Sending message to {0}", dest))

    def quit(self):
        self.active = False


if __name__ == '__main__':
    if len(sys.argv) == 8:
        id = int(sys.argv[1])
        addr = sys.argv[2]
        port = int(sys.argv[3])
        acceptor = Acceptor(
            id, addr, port, sys.argv[4], int(sys.argv[5]), sys.argv[6], int(sys.argv[7]))
        try:
            acceptor.start()
        except KeyboardInterrupt:
            print('quitting...')
            acceptor.quit()
        
    else:
        print("Usage: ...")
