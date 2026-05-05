from queue import Queue
from lib.logger import Logger
from lib.common.definitions import Address, LoggerDetails
from lib.event.segment_event import SegmentEvent
from lib.file_manager.file_manager import FileManager
from lib.protocol.enums import ClientType
from lib.protocol.protocol import Protocol
from lib.protocol.receiver import Receiver
from lib.protocol.sender import Sender
from lib.protocol.socket import Socket
from lib.state.state_context import StateContext
from lib.state.sync_state_server import SyncStateServer
from lib.segment.segment import Segment
from lib.time.busy_wait_timer import BusyWaitTimer
from lib.utils.atomic_map import AtomicMap
from lib.segment.server_segment_service import ServerSegmentService
from lib.segment.segment_service import SegmentService

_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


class AcceptorProtocol:
    def __init__(
        self,
        socket: Socket,
        protocols: AtomicMap[Address, tuple[Queue, Protocol]],
        fileManager: FileManager,
        loggerDetails: LoggerDetails
    ):
        self.socket: Socket = socket
        self.protocols: AtomicMap[Address, tuple[Queue, Protocol]] = protocols
        self.fileManager: FileManager = fileManager
        self.loggerDetails = loggerDetails
        self.logger = Logger("[AcceptorProtocol]", *loggerDetails)
        self.socket.setTimeout(1)

    def _sendErrorAndClose(
            self,
            socket: Socket,
            peerAddress,
            segment: Segment,
            service: ServerSegmentService,
            description: str = ""):
        socket.sendTo(peerAddress, service.makeErrorSegment(
            segment, description))
        socket.close()

    def getFileSize(self, clientType: ClientType, fileName: str, segment: Segment, service: ServerSegmentService):
        if clientType == ClientType.DOWNLOAD:
            fileReader = self.fileManager.openReader(fileName)
            fileSize = fileReader.getFileSize()
            self.fileManager.releaseForReader(fileName)
            return fileSize
        else:
            return service.getFileSizeFromPayload(segment)

    def checkProtocolData(self, synack, peerAddress, protocols):
        protocolData = protocols.get(peerAddress)
        self.logger.info(f"Protocol data for {peerAddress}: {protocolData}")
        if protocolData is not None and not protocolData[1].isHalt():
            protocolData[0].put(SegmentEvent(synack, peerAddress))
            raise Exception

    def registerProtocol(self, address, queue, protocol, protocols):
        protocols[address] = (queue, protocol)

    def reap(self):
        def reapOnProtocols(protocols: dict[Address, tuple[Queue, Protocol]]):
            toRemove = [
                addr for addr, (_, p) in protocols.items()
                if p.isHalt()
            ]

            for addr in toRemove:
                protocols.pop(addr)

            self.logger.info(f"New protocols size: {len(protocols)}")

        self.protocols.callOnMap(lambda p: reapOnProtocols(p))

    def accept(self) -> Protocol | None:
        segment, peerAddress = self.socket.recvFrom(Segment.SIZE_MAX_SEG)
        self.logger.info(
            f"Received SYN packet from {
                peerAddress[0]}:{
                peerAddress[1]}, flags: {
                segment.flags}, payload: {
                    segment.getPayload()[
                        4:].decode('utf-8')}")
        clientType, protocolType = SegmentService.getTypes(segment)
        service = ServerSegmentService(clientType, protocolType)

        synack = service.makeSynAckSegment(segment)
        self.protocols.callOnMap(lambda protocols: self.checkProtocolData(
            synack, peerAddress, protocols))

        ip = self.socket.getIp()
        newSocket = Socket(ip)
        newSocket.setTimeout(1)

        fileName = service.getFileNameFromPayload(segment)

        try:
            fileSize = self.getFileSize(clientType, fileName, segment, service)
        except Exception as e:
            self.logger.error(f"Unable to get FileSize: {e}")
            self._sendErrorAndClose(
                newSocket, peerAddress, segment, service, f"{e}")
            return None

        if clientType == ClientType.DOWNLOAD and not self.fileManager.fileExists(fileName):
            self._sendErrorAndClose(
                newSocket, peerAddress, segment, service, f"File {fileName} does not exist")
            return None

        if clientType == ClientType.UPLOAD and fileSize > _MAX_BYTES:
            self._sendErrorAndClose(
                newSocket, peerAddress, segment, service, f"File {fileName} is too large")
            return None

        eventQueue = Queue()
        eventQueue.put(SegmentEvent(synack, peerAddress))
        sender = Sender(newSocket, self.loggerDetails)
        protocol = Protocol(
            peerAddress,
            peerAddress,
            sender,
            Receiver(newSocket, eventQueue, self.loggerDetails),
            clientType,
            protocolType
        )
        ctx = StateContext(protocol, eventQueue,
                           BusyWaitTimer(), self.loggerDetails, service)

        self.logger.info(
            f"Connection request for file '{fileName}' of size {fileSize} bytes,"
            f" client type: {clientType}, protocol type: {protocolType}"
        )
        protocol.changeState(SyncStateServer(ctx, (fileName, fileSize)))

        self.reap()
        self.protocols.callOnMap(lambda p: self.registerProtocol(
            peerAddress, eventQueue, protocol, p))
        return protocol

    def getLogger(self):
        return self.logger

    def close(self):
        # TODO: Enviar un AbortEvent a cada queue guardada para que entren a FinState
        self.socket.close()
