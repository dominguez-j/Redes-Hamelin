from lib.segment.segment import Segment
from lib.event.segment_event import SegmentEvent
from lib.common.constants import RTO_SECONDS
from lib.common.definitions import Address


class ProtocolState:
    def sendFile(self, fileManager):
        raise NotImplementedError(
            "ProtocolState children classes must implement the `sendFile` method")

    def downloadFile(self, fileManager) -> bytes:
        raise NotImplementedError(
            "ProtocolState children classes must implement the `downloadFile` method")

    def isHalt(self):
        return False

    def sendFin(self, sequenceNumber: int, finState):
        fin = self.ctx.getSegmentService().makeFinSegment(sequenceNumber)
        self.ctx.put(SegmentEvent(fin, None))
        self.ctx.changeState(finState)
        self.logger.info(f"Transitioning to FinState seq={sequenceNumber}")

    def sendAck(self, sequenceNumber: int):
        ack = self.ctx.getSegmentService().makeAckSegment(sequenceNumber)
        self.ctx.sendTo(ack, self.ctx.getPeerAddress())
        self.logger.info(f"Sent ACK seq={sequenceNumber}")

    def sendTo(self, segment: Segment, addr: Address):
        self.ctx.sendTo(segment, addr)

    def isTermination(self, segment: Segment):
        return segment.isFin() or segment.isErr()

    def scheduleTimeout(self, event):
        self.ctx.schedule(RTO_SECONDS, event)

    def cancelTimeout(self, event):
        self.ctx.cancel(event.getName())

    def put(self, event):
        self.ctx.put(event)

    def changeState(self, newState):
        self.ctx.changeState(newState)
