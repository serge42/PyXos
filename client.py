import pickle
import socket
import socket
import sys
import time

from message import *
from socket_helper import getUDPMulticastSocket as create_socket


class Client:
    def __init__(self, id, listen_addr, listen_port, proposers_addr, proposers_port):
        self.id = id
        self.address = (listen_addr, listen_port)
        self.proposers = (proposers_addr, proposers_port)
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                         socket.IPPROTO_UDP)  # IP, UDP

    def start(self):
        self.command_reader()

    def command_reader(self):
        try:
            while True:
                value = input()  # wait for client request
                # send value to proposers
                message = Message(Indicators.CLIENTS, value)
                self.send_message(message, self.proposers)
                # Wait for answer (concurrently)
        except EOFError as e:
            print("Reached EOF, quitting...")
            exit(0)
        except Exception as e:
            print("{0} exception: {1}".format(type(e), e))
            exit(100)
        except KeyboardInterrupt:
            print("quiting")

    def send_message(self, msg, dest):
        print("sent {0} to {1}".format(msg.msg, dest) )
        self.send_socket.sendto(pickle.dumps(msg), dest)

if len(sys.argv) == 6:
    id = sys.argv[1]
    addr = sys.argv[2]
    port = int(sys.argv[3])
    c = Client(
        id, addr, port, sys.argv[4], int(sys.argv[5]))
    c.start()
else:
    print("Usage: ...")
