from lib.common.definitions import Address
from lib.event.segment_event import SegmentEvent
from lib.event.segment_timeout_event import SegmentTimeoutEvent
from lib.file_manager.file_manager import FileManager
from lib.state.halt_state import HaltState
from lib.state.flow_state_factoy import FlowStateFactory as FSFactory
from lib.state.protocol_state import ProtocolState
from lib.state.fin_state import FinState
from lib.state.state_context import StateContext
from lib.segment.client_segment_service import ClientSegmentService
from lib.logger import Logger


class SyncStateClient(ProtocolState):

    def __init__(self, ctx: StateContext, fileName: str):
        self.ctx: StateContext = ctx
        self.segmentService: ClientSegmentService = self.ctx.getSegmentService()
        self.fileName: str = fileName
        self.acceptorAddress: Address = ctx.getPeerAddress()
        self.logger = Logger("[SyncStateClient]", *self.ctx.getLoggerDetails())
        self.expectingData = False

    def handleSegmentForSendFile(self, event: SegmentEvent, fileSize: int):
        segment, address = event.getSegment(), event.getAddr()
        self.ctx.setPeerAddress(address)
        if segment.isAck() and segment.getSequenceNumber() == 0:
            self.changeToFlowState(fileSize, 1)
        elif segment.isFin():
            self.sendFin(1, FinState(self.ctx))
        elif segment.isErr():
            self.logger.error(
                f"Server error: {ClientSegmentService.getErrorMessage(segment)}")
            self.changeState(HaltState())

    def changeToFlowState(self, fileSize: int, baseNumber: int):
        self.changeState(FSFactory.create(
            self.ctx, (self.fileName, fileSize), baseNumber))

    def sendFile(self, fileManager: FileManager):
        fileReader = fileManager.openReader(self.fileName)
        fileSize = fileReader.getFileSize()
        fileManager.releaseForReader(self.fileName)
        synpack = self.segmentService.makeSynpackForUpload(
            self.fileName, fileSize)

        self.logger.info(
            f"Sending SYN packet to {self.acceptorAddress},"
            f"flags: {synpack.flags},"
            f"payload: {synpack.getPayload()[4:].decode('utf-8')}"
        )

        while True:
            self.sendTo(synpack, self.acceptorAddress)
            self.scheduleTimeout(SegmentTimeoutEvent(0))

            event = self.ctx.get()
            if isinstance(event, SegmentTimeoutEvent):
                self.logger.info(f"Timeout received: {event}")
                continue
            elif isinstance(event, SegmentEvent):
                self.handleSegmentForSendFile(event, fileSize)
                break

    def downloadFile(self, _: FileManager):
        synpack = self.segmentService.makeSynpackForDownload(self.fileName)
        synpackTimeoutEvent = SegmentTimeoutEvent(0)
        fileSize = None

        while True:
            if not self.expectingData:
                self.sendTo(synpack, self.acceptorAddress)
                self.scheduleTimeout(synpackTimeoutEvent)

            event = self.ctx.get()
            if (isinstance(event, SegmentTimeoutEvent) and event.getSegmentSequenceNumber() == 0):
                continue

            elif not isinstance(event, SegmentEvent):
                continue

            seg, addr = event.getSegment(), event.getAddr()
            if seg.isErr():
                self.logger.error(
                    f"Server error: {ClientSegmentService.getErrorMessage(seg)}")
            if self.isTermination(seg):
                self.logger.debug(
                    f"Disconnector Address: {self.ctx.getDisconnectorAddress()}")
                self.sendFin(seg.getSequenceNumber() + 1, FinState(self.ctx))
                break

            self.cancelTimeout(synpackTimeoutEvent)

            if seg.isAck() and seg.isSyn() and seg.getSequenceNumber() == 0:

                self.logger.info("Received file size")

                self.ctx.setPeerAddress(addr)
                fileSize = self.segmentService.getFileSizeFromSynSegmentForDownload(
                    seg)
                self.expectingData = True

                self.logger.info(f"File size: {fileSize}")

                synAck = self.segmentService.makeSynAckForPayloadSize()
                self.sendTo(synAck, self.ctx.getPeerAddress())
                self.logger.info(f"Sending SYN-ACK: {synAck}")

            if self.expectingData and not seg.isSyn() and seg.getPayloadLength() > 0:
                self.logger.info(
                    f"Received data segment. Seq = {seg.getSequenceNumber()}")
                self.put(SegmentEvent(seg, self.ctx.getPeerAddress()))
                self.changeToFlowState(fileSize, 1)
                self.logger.info("Switched to FlowState")
                break
