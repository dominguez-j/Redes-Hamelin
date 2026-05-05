from typing import Dict
from lib.common.definitions import FileDetails
from lib.event.event import Event
from lib.event.segment_event import SegmentEvent
from lib.event.segment_timeout_event import SegmentTimeoutEvent
from lib.file_manager.file_manager import FileManager
from lib.file_manager.file_reader import FileReader
from lib.file_manager.file_writer import FileWriter
from lib.logger import Logger
from lib.state.fin_state import FinState
from lib.state.halt_state import HaltState
from lib.state.protocol_state import ProtocolState
from lib.state.state_context import StateContext
from lib.segment.segment import Segment
from lib.event.abort_event import AbortEvent
from lib.segment.segment_service import SegmentService


class PacketInFlight:
    def __init__(self, segment: Segment):
        self.segment = segment
        self.sequenceNumber = segment.getSequenceNumber()


class FlowState(ProtocolState):

    def __init__(
            self,
            ctx: StateContext,
            fileDeatails: FileDetails,
            baseNumber: int,
            windowSize: int,
            receiveWindowSize: int
            ):
        self.ctx: StateContext = ctx
        self.fileDetails: FileDetails = fileDeatails
        self.logger: Logger = Logger(
            "[FlowState]", *self.ctx.getLoggerDetails())
        self.peerAddress = self.ctx.getPeerAddress()
        self.chunkCounter: int = 0
        self.initialSequenceNumber: int = baseNumber
        self.baseNumber: int = baseNumber
        self.nextSequenceNumber: int = baseNumber
        self.packetsInFlight: Dict[int, PacketInFlight] = {}
        self.recvBaseNumber: int = baseNumber
        self.receiveBuffer: Dict[int, Segment] = {}
        self.downloadedBytes: int = 0
        self.finReceived: bool = False
        self.finSequenceNumber: int | None = None
        self.finished = False
        self.windowSize = windowSize
        self.receiveWindowSize = receiveWindowSize
        self.segmentService = self.ctx.getSegmentService()
        self.aborted = False

    def sendFile(self, fileManager: FileManager):
        fileReader = None
        error = False
        totalChunks = 0
        chunks = []
        try:
            fileReader: FileReader = fileManager.openReader(
                self.fileDetails[0])
            self.logger.debug(
                f"FILE SIZE: {self.fileDetails[1]} FILE NAME: {self.fileDetails[0]}"
            )
            chunks = fileReader.readAllChunks(Segment.MAX_PAYLOAD_SIZE)
            totalChunks: int = len(chunks)
            self.logger.debug(f"Total chunks: {totalChunks}")
            self.logger.debug(f"File size: {self.fileDetails[1]}")
        except Exception as e:
            self.logger.error("File Reader Exception: ", e)
            error = True

        while (totalChunks > self.baseNumber - self.initialSequenceNumber) and not error:
            packets: list[PacketInFlight] = self.makeWindow(
                chunks, totalChunks)
            self.sendWindow(packets)

            event = self.ctx.get()

            if isinstance(event, SegmentEvent):
                seg = event.getSegment()

                if seg.isErr():
                    self.logger.error(
                        f"Error during flow: {SegmentService.getErrorMessage(seg)}")
                    error = True
                if self.isTermination(seg):
                    break
                if not seg.isAck() or seg.isSyn():
                    self.logger.info(
                        "Received non-ACK or SYN segment... ignoring")
                    continue

                self.handleAck(event)

            elif isinstance(event, SegmentTimeoutEvent):
                seq_number = event.getSegmentSequenceNumber()
                self.handleTimeout(seq_number)

            elif isinstance(event, AbortEvent):
                self.abort()
                break

        if not error:
            self.logger.info("File sent successfully")
            for sequenceNumber in list(self.packetsInFlight.keys()):
                self.cancelTimeout(SegmentTimeoutEvent(sequenceNumber))
        if not self.aborted:
            self.sendFin(self.nextSequenceNumber, FinState(self.ctx))
        else:
            self.logger.error("ERROR EN UPLOAD")

        if fileReader is not None:
            self.logger.info("Preparing to close file reader")
            fileManager.releaseForReader(self.fileDetails[0])

    def makeWindow(self, chunks: list[bytes], totalChunks: int) -> list[PacketInFlight]:
        packets: list[PacketInFlight] = []
        while (totalChunks > self.nextSequenceNumber - self.initialSequenceNumber) and (
            self.windowSize > len(self.packetsInFlight) + len(packets)
        ):
            payload: bytes = chunks[
                self.nextSequenceNumber - self.initialSequenceNumber
            ]
            seq: int = self.nextSequenceNumber

            segment = self.segmentService.makeSegment(seq, 0, payload)
            self.nextSequenceNumber += 1
            packets.append(PacketInFlight(segment))

        return packets

    def sendWindow(self, packets: list[PacketInFlight]):
        for packet in packets:
            self.sendTo(packet.segment, self.peerAddress)
            self.packetsInFlight[packet.sequenceNumber] = packet
            self.scheduleTimeout(SegmentTimeoutEvent(packet.sequenceNumber))
            self.logger.debug(
                f"Sending segment... to: {self.peerAddress} Seq: {packet.sequenceNumber}")

    def handleAck(self, event: SegmentEvent):
        seqNumberAck = event.getSegment().getSequenceNumber()

        if seqNumberAck not in self.packetsInFlight:
            self.logger.info(f"Duplicate or old ACK seq={seqNumberAck}")
            return

        self.logger.info(f"Received ACK for seq={seqNumberAck}")
        self.packetsInFlight.pop(seqNumberAck)
        self.cancelTimeout(SegmentTimeoutEvent(seqNumberAck))

        while (self.baseNumber not in self.packetsInFlight) and (
            self.nextSequenceNumber > self.baseNumber
        ):
            self.baseNumber += 1

    def handleTimeout(self, seq_number: int):
        self.logger.info(f"Timeout for seq: {seq_number}")
        packet = self.packetsInFlight.get(seq_number)

        if packet is None:
            self.logger.info(
                f"Timeout for seq={seq_number} but packet already acknowledged"
            )
            return
        self.sendTo(packet.segment, self.peerAddress)
        self.logger.info(f"Re-sending segment... Seq: {packet.sequenceNumber}")
        self.scheduleTimeout(SegmentTimeoutEvent(packet.sequenceNumber))

    def downloadFile(self, fileManager: FileManager):
        self.logger.debug(f"File details: {self.fileDetails}")
        fileWriter = None
        try:
            fileWriter: FileWriter = fileManager.openWriter(
                self.fileDetails[0], self.fileDetails[1]
            )
            while not self.finished:
                event = self.ctx.get()

                if isinstance(event, AbortEvent):
                    self.abort()
                    continue
                if not isinstance(event, SegmentEvent):
                    assert isinstance(event, Event)
                    self.logger.info(
                        f"Received unexpected event {event.getName()}... ignoring"
                    )
                    continue

                seg = event.getSegment()

                self.handleSegmentReceived(seg, fileWriter)
                self.logger.debug(
                    f"Downloaded bytes: {self.downloadedBytes}/{self.fileDetails[1]}"
                )
                self.logger.debug(f"FINISHED: {self.finished}")
                if self.finReceived and self.downloadedBytes >= self.fileDetails[1]:
                    self.finished = True
                    self.logger.debug(f"FINISHED: {self.finished}")
        except Exception as e:
            self.logger.error(f"Exception occurred: {e}")
        finally:
            if fileWriter is not None:
                fileWriter.close()
                fileManager.release(self.fileDetails[0])
                self.logger.info("Closing file writer")
            if not self.aborted:
                self.sendFin(self.finSequenceNumber or 0, FinState(self.ctx))

    def handleSegmentReceived(self, segment: Segment, fileWriter: FileWriter):
        seqNumber = segment.getSequenceNumber()

        if segment.isAck():
            self.logger.info(
                f"Received ACK while receiving file... ignoring seq={seqNumber}"
            )
            return

        if segment.isErr():
            self.logger.error(
                f"Error during flow: {SegmentService.getErrorMessage(segment)}")
        if self.isTermination(segment):
            self.logger.info(f"Received FIN seq={seqNumber}")
            self.finReceived = True
            self.finSequenceNumber = seqNumber

            if self.downloadedBytes < self.fileDetails[1]:
                self.logger.info(
                    f"FIN received but file is not complete yet: "
                    f"{self.downloadedBytes}/{self.fileDetails[1]} bytes"
                )
            return

        if seqNumber < self.recvBaseNumber:
            self.logger.info(
                f"Duplicate old packet seq={seqNumber}. Re-ACKing")
            self.sendAck(seqNumber)
            return

        if not self.isInReceiveWindow(seqNumber):
            self.logger.info(
                f"Packet seq={seqNumber} outside receive window. Window base: {self.recvBaseNumber}")
            return

        if seqNumber in self.receiveBuffer:
            self.logger.info(
                f"Duplicate buffered packet seq={seqNumber}. Re-ACKing")
            self.sendAck(seqNumber)
            return

        self.logger.info(
            f"Received DATA seq={seqNumber}, len={segment.getPayloadLength()}"
        )

        self.receiveBuffer[seqNumber] = segment
        self.sendAck(seqNumber)

        self.writeContiguousPackets(fileWriter)

    def isInReceiveWindow(self, seqNumber: int) -> bool:
        return (
            self.recvBaseNumber <= seqNumber < self.recvBaseNumber + self.receiveWindowSize
        )

    def writeContiguousPackets(self, fileWriter: FileWriter):
        chunksToWrite: list[bytes] = []
        bytesToWrite = 0

        while self.recvBaseNumber in self.receiveBuffer:
            segment = self.receiveBuffer.pop(self.recvBaseNumber)
            payload = segment.getPayload()

            chunksToWrite.append(payload)
            bytesToWrite += len(payload)

            self.logger.info(f"Ready to write seq={self.recvBaseNumber}")
            self.recvBaseNumber += 1

        if not chunksToWrite:
            return

        fileWriter.writeBatch(self.downloadedBytes, chunksToWrite)
        self.downloadedBytes += bytesToWrite

        self.logger.info(
            f"Written {bytesToWrite} bytes. Total downloaded={self.downloadedBytes}"
        )

    def abort(self):
        self.finished = True
        self.aborted = True
        self.changeState(HaltState())
