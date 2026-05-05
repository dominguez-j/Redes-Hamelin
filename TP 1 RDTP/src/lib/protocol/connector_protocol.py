from queue import Queue
from lib.time.busy_wait_timer import BusyWaitTimer
from lib.state.sync_state_client import SyncStateClient
from lib.protocol.socket import Socket
from lib.segment.client_segment_service import ClientSegmentService
from lib.protocol.enums import ClientType, ProtocolType
from lib.protocol.sender import Sender
from lib.protocol.receiver import Receiver
from lib.protocol.protocol import Protocol
from lib.state.state_context import StateContext
from lib.common.definitions import Address, LoggerDetails
from lib.logger import Logger


class ConnectorProtocol:
    def __init__(
        self,
        socket: Socket,
        ctype: ClientType,
        ptype: ProtocolType,
        fileName: str,
        loggerDetails: LoggerDetails
    ):
        self.socket: Socket = socket
        self.clientType: ClientType = ctype
        self.protocolType: ProtocolType = ptype
        self.fileName: str = fileName
        self.loggerDetails: LoggerDetails = loggerDetails
        self.logger = Logger("[ConnectorProtocol]", *loggerDetails)

    def connect(self, addr: Address) -> Protocol:
        eventQueue = Queue()
        sender = Sender(self.socket, self.loggerDetails)
        receiver = Receiver(self.socket, eventQueue, self.loggerDetails)
        disconnectorAddress = (addr[0], addr[1] + 1)

        self.logger.info(f"Local address: {self.socket.getAddr()}")

        protocol = Protocol(addr, disconnectorAddress, sender,
                            receiver, self.clientType, self.protocolType)
        ctx = StateContext(protocol, eventQueue, BusyWaitTimer(
        ), self.loggerDetails, ClientSegmentService(self.clientType, self.protocolType))
        state = SyncStateClient(ctx, self.fileName)
        protocol.changeState(state)
        return protocol

    def close(self):
        self.socket.close()
