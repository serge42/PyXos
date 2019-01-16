import socket

def getUDPMulticastSocket(address_port):
    address, _ = address_port

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                      socket.IPPROTO_UDP)  # IP, UDP
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    s.bind(address_port)  # Binding to multicast
    # print(socket.gethostname())
    host = socket.gethostbyname(socket.gethostname())
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                 socket.inet_aton(host))
    s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                 socket.inet_aton(address) + socket.inet_aton(host))

    return s
