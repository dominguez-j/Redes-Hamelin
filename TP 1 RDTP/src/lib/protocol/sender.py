from lib.segment.segment import Segment
from lib.protocol.socket import Socket
from lib.common.definitions import Address, LoggerDetails
from lib.logger import Logger


class Sender:
    def __init__(self, socket: Socket, loggerDetails: LoggerDetails):
        self.socket = socket
        self.logger = Logger("[SENDER]", *loggerDetails)

    def sendTo(self, segment: Segment, addr: Address):
        try:
            self.socket.sendTo(addr, segment)
        except Exception as e:
            self.logger.debug(f"Received an exception: {e}")
