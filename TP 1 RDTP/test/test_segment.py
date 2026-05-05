import unittest

from lib.segment.segment import Segment


class TestSegment(unittest.TestCase):
    def setUp(self):
        sequenceNumber = 1
        payloadLength = 5
        flags = 38          # 0b00100110
        payload = b"hello"  # 26725 + 27756 + 111
        # Checksum  = ~(1 + 160 + 38 + 26725 + 27756 + 111)
        #           =  ~54791
        #           = 10744
        self.segment = Segment(sequenceNumber, payloadLength, flags, payload)

    def testFromBytes(self):
        result = Segment.fromBytes(self.segment.toBytes())
        self.assertEqual(self.segment, result)

    def testToBytes(self):
        self.segment.toBytes()

    def testBijection(self):
        self.assertEqual(Segment.fromBytes(self.segment.toBytes()), self.segment)

    def testIsSyn(self):
        self.assertTrue(self.segment.isSyn())

    def testIsAck(self):
        self.assertFalse(self.segment.isAck())

    def testIsErr(self):
        self.assertFalse(self.segment.isErr())

    def testGetCtyp(self):
        self.assertTrue(self.segment.getCtyp())

    def testGetPtyp(self):
        self.assertTrue(self.segment.getPtyp())

    def testIsFin(self):
        self.assertFalse(self.segment.isFin())

    def testPayloadLength(self):
        self.assertEqual(self.segment.getPayloadLength(), 5)

    def testPayload(self):
        self.assertEqual(self.segment.getPayload(), b"hello")

    def testSequenceNumber(self):
        self.assertEqual(self.segment.getSequenceNumber(), 1)

    def testChecksum(self):
        self.assertEqual(self.segment.getChecksum(), 10744)


if __name__ == '__main__':
    unittest.main()
