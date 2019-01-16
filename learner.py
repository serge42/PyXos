import pickle
import select
import socket
import sys
import time

from message import *
from socket_helper import getUDPMulticastSocket as create_socket


class Learner:
    def __init__(self, id, listen_addr, listen_port, acceptors_addr, acceptors_port):
        self.id = id
        self.listen_addr = (listen_addr, listen_port)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                         socket.IPPROTO_UDP)  # IP, UDP

        self.active = True
        self.s = create_socket(self.listen_addr)
        self.learned = {}

    def start(self):
        self.run()

    def run(self):
        
        req = Message(Indicators.LEARNERS_REQ, '')
        self.send_message(req, self.listen_addr)
        pending2b = {}
        known_acceptors = []
        timeout = .1 # second
        try:
            while self.active:
                ready = select.select([self.s], [], [], timeout)
                if not ready[0]:
                    continue

                data, addr = self.s.recvfrom(4096)  # buffer size
                msg = pickle.loads(data)

                if msg.indicator == Indicators.ACCEPTORS and not msg.msg in known_acceptors:
                    if not msg.msg in known_acceptors:
                        known_acceptors.append(msg.msg)

                elif msg.indicator == Indicators.PHASE2B:
                    phase2b = msg.msg
                    b = phase2b.ballot_num
                    if phase2b.acceptor_id not in known_acceptors:
                        known_acceptors.append(phase2b.acceptor_id)
                    if not b in self.learned:
                        if not b in pending2b:
                            pending2b[b] = ([], phase2b.value)
                        acceptor_list = pending2b[b][0]
                        if not phase2b.acceptor_id in acceptor_list:
                            acceptor_list.append(phase2b.acceptor_id)
                        pending2b[b] = (acceptor_list, pending2b[b][1])
                        if len(pending2b[b][0]) > len(known_acceptors)/2:
                            print("[L{0}]> ballot {1} -> [{2}]".format(self.id, b, pending2b[b][1]))
                            self.learned[b] = pending2b[b][1]
                            pending2b.pop(b)

                elif msg.indicator == Indicators.LEARNERS_REQ:
                    for i in self.learned:
                        learned_msg = Message(Indicators.LEARNERS_REP, (i, self.learned[i]) )
                        self.send_message(learned_msg, self.listen_addr)
                elif msg.indicator == Indicators.LEARNERS_REP:
                    # print("[L{0}]> recvd rep: updating learned...".format(self.id))
                    i, val = msg.msg
                    if not i in self.learned:
                        self.learned[i] = val
                        print("[L{0}]> ballot {1} -> [{2}]".format(self.id, i, val))
            # end while
            self.s.close() 
        except Exception as e:
            print("{0} exception: {1}".format(type(e), e))
            self.s.close()

    def send_message(self, msg, dest):
        self.send_socket.sendto(pickle.dumps(msg), dest)

    def quit(self):
        self.active = False


if len(sys.argv) == 6:
    id = sys.argv[1]
    addr = sys.argv[2]
    port = sys.argv[3]
    l = Learner(
        id, addr, int(port), sys.argv[4], int(sys.argv[5]))
    try:
        l.start()
    except KeyboardInterrupt:
        print('quitting...')
        l.quit()
else:
    print("Usage: ...")
