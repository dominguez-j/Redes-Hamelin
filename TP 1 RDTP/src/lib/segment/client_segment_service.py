from lib.protocol.enums import ClientType, ProtocolType
from lib.segment.segment import Segment
from lib.segment.segment_service import SegmentService


class ClientSegmentService(SegmentService):
    def __init__(self, clientType: ClientType, protocolType: ProtocolType):
        super().__init__(clientType, protocolType)

    def makeSynpackForUpload(self, fileName: str, fileSize: int):
        fileNameInBytes = fileName.encode("utf-8")
        fileSizeInBytes = int(fileSize).to_bytes(4, "big")
        return Segment(
            0,
            4 + len(fileNameInBytes),
            Segment.SYN_MASK | super().getMasks(),
            fileSizeInBytes + fileNameInBytes,
        )

    def makeSynpackForDownload(self, fileName: str):
        fileNameInBytes = fileName.encode("utf-8")
        fileSizeInBytes = int(0).to_bytes(4, "big")
        return Segment(
            0,
            4 + len(fileNameInBytes),
            Segment.SYN_MASK | super().getMasks(),
            fileSizeInBytes + fileNameInBytes,
        )

    def makeSynAckForPayloadSize(self):
        return Segment(
            0,
            0,
            Segment.SYN_MASK | Segment.ACK_MASK | super().getMasks(),
            b""
        )

    def getFileSizeFromSynSegmentForDownload(self, segment: Segment):
        return int.from_bytes(segment.getPayload(), "big")
