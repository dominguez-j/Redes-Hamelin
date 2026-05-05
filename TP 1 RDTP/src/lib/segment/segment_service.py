from lib.protocol.enums import ClientType, ProtocolType
from lib.segment.segment import Segment


class SegmentService:
    def __init__(self, clientType: ClientType, protocolType: ProtocolType):
        self.ctypMask = 0
        self.ptypMask = 0

        self.setCtypMask(clientType)
        self.setPtypMask(protocolType)

    def setCtypMask(self, clientType: ClientType):
        self.ctypMask = Segment.CTYP_MASK if clientType == ClientType.DOWNLOAD else 0

    def setPtypMask(self, protocolType: ProtocolType):
        self.ptypMask = (
            Segment.PTYP_MASK if protocolType == ProtocolType.SELECTIVE_REPEAT else 0
        )

    def getMasks(self):
        return self.ctypMask | self.ptypMask

    @staticmethod
    def getTypes(segment: Segment):
        return (
            ClientType.DOWNLOAD if segment.getCtyp() else ClientType.UPLOAD,
            ProtocolType.SELECTIVE_REPEAT if segment.getPtyp() else ProtocolType.STOP_AND_WAIT
        )

    @staticmethod
    def getErrorMessage(segment: Segment):
        return segment.getPayload().decode("utf-8")

    def getFileNameFromPayload(self, segment: Segment):
        return segment.getPayload()[4:].decode("utf-8")

    def getFileSizeFromPayload(self, segment: Segment):
        return int.from_bytes(segment.getPayload()[:4], "big")

    def makeFileSizeFromBytesCount(self, fileSize: int):
        return fileSize.to_bytes(4, "big")

    def makeUploadSynpack(self, fileName: str, fileSize: int):
        flags = Segment.SYN_MASK | self.getMasks()
        fileNameSize = len(fileName) & 0xFF
        fileSizeBytes = self.makeFileSizeFromBytesCount(fileSize)
        return Segment(
            0,
            5 + len(fileName),
            flags,
            fileNameSize.to_bytes(1, "big") + fileName.encode("utf-8") + fileSizeBytes
        )

    def makeDownloadSynpack(self, fileName: str):
        flags = Segment.SYN_MASK | self.getMasks()
        fileNameSize = len(fileName) & 0xFF
        return Segment(
            0,
            1 + len(fileName),
            flags,
            fileNameSize.to_bytes(1, "big") + fileName.encode("utf-8"),
        )

    def makeSynSegment(self, sequenceNumber: int, fileName: str, fileSize: int):
        flags = Segment.SYN_MASK | self.getMasks()
        return Segment(
            sequenceNumber,
            4 + len(fileName),
            flags,
            self.makeFileSizeFromBytesCount(
                fileSize) + fileName.encode("utf-8"),
        )

    def makeAckSegment(self, sequenceNumber: int):
        return Segment(sequenceNumber, 0, Segment.ACK_MASK | self.getMasks(), b"")

    def makeSynAckPayloadSegment(
        self, sequenceNumber: int, fileName: str, fileSize: int
    ):
        return Segment(
            sequenceNumber,
            4 + len(fileName),
            Segment.SYN_MASK | Segment.ACK_MASK | self.getMasks(),
            self.makeFileSizeFromBytesCount(
                fileSize) + fileName.encode("utf-8"),
        )

    def makeAckFinSegment(self, segment: Segment):
        return Segment(
            segment.getSequenceNumber(), 0, Segment.ACK_MASK | Segment.FIN_MASK | self.getMasks(), b""
        )

    def makeSynAckSegment(self, segment: Segment, fileSize: int = None):
        flags = Segment.SYN_MASK | Segment.ACK_MASK | self.getMasks()
        return Segment(
            segment.getSequenceNumber() + 1,
            0 if fileSize is None else 4,
            flags,
            b"" if fileSize is None else self.makeFileSizeFromBytesCount(
                fileSize),
        )

    def makeErrorSegment(self, segment: Segment, description: str = ""):
        flags = Segment.ERR_MASK | self.getMasks()
        return Segment(
            segment.getSequenceNumber(), 0, flags, description.encode("utf-8")
        )

    def makeFinSegment(self, sequenceNumber: int):
        flags = Segment.FIN_MASK | self.getMasks()
        return Segment(sequenceNumber + 1, 0, flags, b"")

    def makeSegment(self, sequenceNumber: int, flags: int, payload: bytes):
        return Segment(
            sequenceNumber, len(payload), flags | self.getMasks(),
            payload
        )
