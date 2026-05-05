from lib.common.definitions import Address
from lib.event.segment_event import SegmentEvent
from lib.event.segment_timeout_event import SegmentTimeoutEvent
from lib.file_manager.file_manager import FileManager
from lib.state.halt_state import HaltState
from lib.state.protocol_state import ProtocolState
from lib.state.state_context import StateContext
from lib.segment.segment_service import SegmentService
from lib.event.abort_event import AbortEvent
from lib.logger import Logger
import threading


class FinState(ProtocolState):
    def __init__(self, ctx: StateContext):
        self.ctx: StateContext = ctx
        self.disconnectorAddress: Address = ctx.getDisconnectorAddress()
        self.segmentService: SegmentService = self.ctx.getSegmentService()
        self.logger = Logger("[FinState]", *self.ctx.getLoggerDetails())

    def handleFin(self):
        finSegment = None
        while True:
            event = self.ctx.get()

            if isinstance(event, AbortEvent):
                self.changeState(HaltState())
                self.logger.debug(
                    f"RECEIVED ABORT EVENT - ADDRESS: {self.ctx.sender.socket.getAddr()}")
                break

            if isinstance(event, SegmentTimeoutEvent) and finSegment is not None:
                if event.getSegmentSequenceNumber() == finSegment.getSequenceNumber():
                    self.sendTo(finSegment, self.disconnectorAddress)
                    self.scheduleTimeout(event)

            elif isinstance(event, SegmentEvent) and (self.isTermination(event.getSegment())):
                if finSegment is None:
                    finSegment = event.getSegment()

                if finSegment.isErr():
                    self.logger.error(
                        f"Finishing with error: {SegmentService.getErrorMessage(finSegment)}")

                if event.getAddr() is None:
                    self.logger.debug(
                        f"Notificed to stop - SENDING TO {self.disconnectorAddress}")
                    self.sendTo(
                        self.segmentService.makeFinSegment(finSegment.getSequenceNumber()),
                        self.disconnectorAddress
                    )
                    self.scheduleTimeout(event)
                elif event.getAddr() == self.disconnectorAddress:
                    self.logger.debug(f"STOPPING {threading.get_native_id()}")
                    self.cancelTimeout(event)
                    self.changeState(HaltState())
                    break

    def sendFile(self, _: FileManager):
        self.handleFin()

    def downloadFile(self, _: FileManager):
        self.handleFin()
