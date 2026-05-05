from lib.segment.segment import Segment
from lib.common.definitions import Address
from lib.event.event import Event


class SegmentEvent(Event):
    def __init__(self, segment: Segment, addr: Address):
        super().__init__("SEGMENT")
        self.segment = segment
        self.addr = addr

    def getSegment(self) -> Segment:
        return self.segment

    def getAddr(self) -> Address:
        return self.addr
