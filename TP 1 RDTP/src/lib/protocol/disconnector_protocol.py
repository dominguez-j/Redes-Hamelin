from queue import Queue
from lib.common.definitions import Address
from lib.protocol.protocol import Protocol
from lib.protocol.socket import Socket
from lib.segment.segment import Segment
from lib.segment.segment_service import SegmentService
from lib.utils.atomic_map import AtomicMap
from typing import Dict
from lib.event.abort_event import AbortEvent
from lib.logger import Logger
from lib.common.definitions import LoggerDetails


class DisconnectorProtocol:
    def __init__(
        self, socket: Socket, protocols: AtomicMap[Address, tuple[Queue, Protocol]], loggerDetails: LoggerDetails
    ):
        self.socket: Socket = socket
        self.protocols: AtomicMap[Address, tuple[Queue, Protocol]] = protocols
        self.socket.setTimeout(1)
        self.logger = Logger("[DisconnectorProtocol]", *loggerDetails)

    def abortProtocol(self, address, protocols: Dict[Address, tuple[Queue, Protocol]]):
        if protocols.get(address) is not None:
            protocols.get(address)[0].put(AbortEvent())

    def disconnect(self):
        try:
            segment, address = self.socket.recvFrom(Segment.SIZE_MAX_SEG)
            if segment is None or address is None:
                return
            self.logger.info("Received segment")

            if segment.isErr():
                self.logger.error(
                    f"Client error: {SegmentService.getErrorMessage(segment)}")

            if segment.isFin() or segment.isErr():
                self.logger.info(f"Fin or Error Received - Address: {address}")
                ctype, ptyp = SegmentService.getTypes(segment)
                service = SegmentService(ctype, ptyp)
                self.protocols.callOnMap(
                    lambda p: self.abortProtocol(address, p))
                self.socket.sendTo(
                    address, service.makeAckFinSegment(segment)
                )
        except Exception as e:
            self.logger.error(f"Exception occurred: {e}")
            pass

    def getLogger(self):
        return self.logger

    def close(self):
        self.socket.close()
