from lib.common.definitions import Address, FileDetails
from lib.event.segment_event import SegmentEvent
from lib.event.segment_timeout_event import SegmentTimeoutEvent
from lib.file_manager.file_manager import FileManager
from lib.state.flow_state_factoy import FlowStateFactory as FSFactory
from lib.state.protocol_state import ProtocolState
from lib.state.fin_state import FinState
from lib.state.state_context import StateContext
from lib.segment.segment import Segment
from lib.segment.server_segment_service import ServerSegmentService
from lib.logger import Logger


class SyncStateServer(ProtocolState):

    def __init__(
        self, ctx: StateContext, fileDetails: FileDetails
    ):
        self.ctx: StateContext = ctx
        self.peerAddress: Address = ctx.getPeerAddress()
        self.segmentService: ServerSegmentService = self.ctx.getSegmentService()
        self.fileDetails = fileDetails
        self.logger = Logger("[SyncStateServer]", *self.ctx.getLoggerDetails())
        self.logger.info(
            f"FILE NAME: {fileDetails[0]}, FILE SIZE: {fileDetails[1]}")

    def getFileDetailsForSendFile(self, fileManager: FileManager) -> FileDetails:
        event = None
        while event is None:
            tempEvent = self.ctx.get()
            if not isinstance(tempEvent, SegmentEvent):
                continue
            seg = tempEvent.getSegment()

            if seg.isErr():
                self.logger.error(
                    f"Client error: {ServerSegmentService.getErrorMessage(seg)}")
            if self.isTermination(seg):
                self.sendFin(seg.getSequenceNumber() + 1, FinState(self.ctx))
                return (None, None)
            if seg.isSyn():
                event = tempEvent
                break

        fileName = event.getSegment().getPayload()[0:].decode("utf-8")
        fileReader = fileManager.openReader(self.fileDetails[0])
        fileSize = fileReader.getFileSize()
        fileManager.releaseForReader(self.fileDetails[0])

        self.logger.info(f"FILE NAME {fileName}, FILE SIZE {fileSize}")
        return (fileName, fileSize)

    def transmitSynAckPayloadSegment(self, synAckPayloadSegment: Segment):
        timeoutEvent = SegmentTimeoutEvent(
            synAckPayloadSegment.getSequenceNumber())
        self.logger.info("Excepting SYN-ACK from SYN-ACK-FILESIZE")
        while True:
            self.scheduleTimeout(timeoutEvent)
            self.sendTo(synAckPayloadSegment, self.peerAddress)

            event = self.ctx.get()
            if isinstance(event, SegmentTimeoutEvent):
                continue
            elif isinstance(event, SegmentEvent):
                seg = event.getSegment()
                if seg.isErr():
                    self.logger.error(
                        f"Client error: {ServerSegmentService.getErrorMessage(seg)}")
                if self.isTermination(seg):
                    self.logger.info("ERROR DURING SYN-ACK")
                    self.sendFin(1, FinState(self.ctx))
                elif seg.isAck() and seg.isSyn() and seg.getSequenceNumber() == 0:
                    self.logger.info("RECEIVED SYN-ACK!!")
                    self.cancelTimeout(timeoutEvent)
                    break

    def sendFile(self, fileManager: FileManager):
        (fileName, fileSize) = self.getFileDetailsForSendFile(fileManager)
        if fileName is None:
            return

        synAckPayload = self.segmentService.makeSynAckPayloadSegmentForUpload(
            fileSize)
        self.transmitSynAckPayloadSegment(synAckPayload)
        self.logger.info(f"FILE NAME: {fileName}, FILE SIZE: {fileSize}")
        self.changeState(FSFactory.create(self.ctx, self.fileDetails, 1))

    def getSegmentForDownloadFile(self):
        event = self.ctx.get()

        if not isinstance(event, SegmentEvent):
            return None
        address = event.getAddr()
        if address != self.peerAddress:
            return None
        return event.getSegment()

    def handleSynSegmentForDownloadFile(self, segment: Segment):
        if len(self.fileDetails[0]) == 0:
            self.fileDetails = self.segmentService.getFileDetailsFromSynSegment(
                segment)
        self.sendTo(
            self.segmentService.makeAckSegmentForDownload(), self.peerAddress
        )

    def handlePayloadForDownloadFile(self, segment: Segment):
        self.changeState(FSFactory.create(self.ctx, self.fileDetails, 1))
        self.put(SegmentEvent(segment, self.peerAddress))

    def downloadFile(self, _: FileManager):
        while True:

            segment = self.getSegmentForDownloadFile()
            if segment is None:
                continue

            if segment.isErr():
                self.logger.error(
                    f"Client error: {ServerSegmentService.getErrorMessage(segment)}")
            if self.isTermination(segment):
                self.sendFin(segment.getSequenceNumber(), FinState(self.ctx))
                break
            elif segment.isSyn():
                self.handleSynSegmentForDownloadFile(segment)
            elif not segment.isSyn() and (segment.getPayloadLength() > 0) and (not segment.isErr()):
                self.handlePayloadForDownloadFile(segment)
                break
