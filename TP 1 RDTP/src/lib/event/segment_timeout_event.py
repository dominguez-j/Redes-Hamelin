from lib.event.event import Event


class SegmentTimeoutEvent(Event):
    def __init__(self, segmentSequenceNumber: int):
        super().__init__("SEGMENT-TIMEOUT-" + str(segmentSequenceNumber))
        self.segmentSequenceNumber: int = segmentSequenceNumber

    def getSegmentSequenceNumber(self) -> int:
        return self.segmentSequenceNumber
