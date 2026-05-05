from lib.common.definitions import FileDetails
from lib.protocol.enums import ClientType, ProtocolType
from lib.segment.segment import Segment
from lib.segment.segment_service import SegmentService


class ServerSegmentService(SegmentService):

    def __init__(self, clientType: ClientType, protocolType: ProtocolType):
        super().__init__(clientType, protocolType)

    def makeSynAckPayloadSegmentForUpload(self, fileSize: int):
        return Segment(
            0,
            4,
            Segment.SYN_MASK | Segment.ACK_MASK | super().getMasks(),
            int(fileSize).to_bytes(4, "big"),
        )

    def getFileDetailsFromSynSegment(self, segment: Segment) -> FileDetails:
        payload = segment.getPayload()
        return (payload[4:].decode("utf-8"), int.from_bytes(bytes(payload[:4]), "big"))

    def makeAckSegmentForDownload(self):
        return Segment(0, 0, Segment.ACK_MASK | super().getMasks(), bytes())
