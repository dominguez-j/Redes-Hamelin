import struct


class Segment:
    SIZE_MAX_SEG = 1400
    FORMAT = "!H H H H"
    PAYLOAD_LENGTH_SHIFT = 5
    FLAGS_MASK = 0x3F  # 0011 1111
    HEADERS_LENGTH = 8
    MAX_PAYLOAD_SIZE = SIZE_MAX_SEG - HEADERS_LENGTH

    # Masks for each bit
    SYN_MASK = 0b00100000
    ACK_MASK = 0b00010000
    ERR_MASK = 0b00001000
    CTYP_MASK = 0b00000100
    PTYP_MASK = 0b00000010
    FIN_MASK = 0b00000001

    def __init__(self, sequenceNumber: int, payloadLength: int, flags: int, payload: bytes):
        self.sequenceNumber = sequenceNumber
        self.payloadLength = payloadLength
        self.flags = flags
        self.payload = payload
        self.checksum = self.calculateChecksum()

    def calculateChecksum(self) -> int:
        twoBytesMask = 0xFFFF
        checksum = self.sequenceNumber
        checksum += self.payloadLength << Segment.PAYLOAD_LENGTH_SHIFT
        checksum += self.flags & Segment.FLAGS_MASK
        i = 0
        while i + 1 < self.payloadLength:
            checksum += struct.unpack("!H", self.payload[i:i + 2])[0]
            i += 2
        if self.payloadLength % 2 != 0:
            checksum += self.payload[-1]
        return ~checksum & twoBytesMask

    def isSyn(self) -> bool:
        return (self.flags & Segment.SYN_MASK) != 0

    def isAck(self) -> bool:
        return (self.flags & Segment.ACK_MASK) != 0

    def isErr(self) -> bool:
        return (self.flags & Segment.ERR_MASK) != 0

    def getCtyp(self) -> int:
        return self.flags & Segment.CTYP_MASK

    def getPtyp(self) -> int:
        return self.flags & Segment.PTYP_MASK

    def isFin(self) -> bool:
        return (self.flags & Segment.FIN_MASK) != 0

    def getPayloadLength(self) -> int:
        return self.payloadLength

    def getPayload(self) -> bytes:
        return self.payload

    def getSequenceNumber(self) -> int:
        return self.sequenceNumber

    def getChecksum(self) -> int:
        return self.checksum

    def toBytes(self) -> bytes:
        return struct.pack(
            Segment.FORMAT,
            self.checksum,
            self.sequenceNumber,
            self.payloadLength << Segment.PAYLOAD_LENGTH_SHIFT,
            self.flags & Segment.FLAGS_MASK
        ) + self.payload

    @staticmethod
    def fromBytes(data: bytes):
        checksum, sequenceNumber, payloadLength, flags = struct.unpack(
            Segment.FORMAT, data[:Segment.HEADERS_LENGTH])
        payloadLength = payloadLength >> Segment.PAYLOAD_LENGTH_SHIFT
        flags = flags & Segment.FLAGS_MASK
        payload = data[Segment.HEADERS_LENGTH:]
        return Segment(sequenceNumber, payloadLength, flags, payload)

    def __eq__(self, other):
        if not isinstance(other, Segment):
            return False
        return (self.sequenceNumber == other.sequenceNumber and
                self.payloadLength == other.payloadLength and
                self.flags == other.flags and
                self.payload == other.payload and
                self.checksum == other.checksum
                )
