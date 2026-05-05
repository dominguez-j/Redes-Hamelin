import socket
from lib.segment.segment import Segment
from lib.common.definitions import Address


class Socket:
    def __init__(self, hostname: str | None = '', port: int | None = 0):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(hostname, port)

    def bind(self, hostname: str, port: int):
        self.socket.bind((hostname, port))

    def connect(self, hostname: str, port: int):
        self.socket.connect((hostname, port))

    def getIp(self):
        return self.socket.getsockname()[0]

    def getPort(self):
        return self.socket.getsockname()[1]

    def getPeerIp(self):
        return self.socket.getpeername()[0]

    def getPeerPort(self):
        return self.socket.getpeername()[1]

    def getAddr(self):
        return self.socket.getsockname()

    def getPeerAddr(self):
        return self.socket.getpeername()

    def recvFrom(self, size: int) -> tuple[Segment, Address]:
        data, address = self.socket.recvfrom(size)
        segment = Segment.fromBytes(data)
        return (segment, address)

    def recv(self, size: int) -> Segment:
        data = self.socket.recv(size)
        segment = Segment.fromBytes(data)
        return segment

    def sendTo(self, address: Address, segment: Segment) -> int:
        return self.socket.sendto(segment.toBytes(), address)

    def send(self, segment: Segment) -> int:
        return self.socket.send(segment.toBytes())

    def close(self):
        self.socket.close()

    def setTimeout(self, timeout: float):
        self.socket.settimeout(timeout)
