import unittest

from lib.protocol.socket import Socket
from lib.segment.segment import Segment


class TestSocket(unittest.TestCase):
    def createSockets(self, firstPort, secondPort):
        firstSocket = Socket("localhost", firstPort)
        secondSocket = Socket("localhost", secondPort)
        return (firstSocket, secondSocket)

    def setUp(self):
        self.s1, self.s2 = self.createSockets(8080, 9000)
        self.segment = Segment(1, 5, 0, b"hello")

    def tearDown(self):
        self.s1.close()
        self.s2.close()

    def testSocketConnection(self):
        self.s1.connect(self.s2.getIp(), self.s2.getPort())
        self.s2.connect(self.s1.getIp(), self.s1.getPort())

    def testSocketSend(self):
        self.s1.sendTo((self.s2.getIp(), self.s2.getPort()), self.segment)

    def testSocketRecv(self):
        self.s1.sendTo((self.s2.getIp(), self.s2.getPort()), self.segment)
        segment, address = self.s2.recvFrom(Segment.SIZE_MAX_SEG)
        self.assertEqual(segment, self.segment)
        self.assertEqual(address, (self.s1.getIp(), self.s1.getPort()))

    def testSocketSendConnected(self):
        self.s1.connect(self.s2.getIp(), self.s2.getPort())
        self.s1.send(self.segment)

    def testSocketRecvConnected(self):
        self.s1.connect(self.s2.getIp(), self.s2.getPort())
        self.s2.connect(self.s1.getIp(), self.s1.getPort())
        self.s1.send(self.segment)
        segment = self.s2.recv(Segment.SIZE_MAX_SEG)
        self.assertEqual(segment, self.segment)


if __name__ == '__main__':
    unittest.main()
