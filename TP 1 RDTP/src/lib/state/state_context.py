from queue import Queue
from lib.protocol.protocol import Protocol
from lib.protocol.sender import Sender
from lib.time.busy_wait_timer import BusyWaitTimer
from lib.common.definitions import LoggerDetails
from lib.segment.segment_service import SegmentService


class StateContext:
    def __init__(
            self,
            protocol: Protocol,
            eventQueue: Queue,
            timer: BusyWaitTimer,
            loggerDetails: LoggerDetails,
            segmentService: SegmentService
    ):
        self.protocol: Protocol = protocol
        self.sender: Sender = protocol.sender
        self.eventQueue: Queue = eventQueue
        self.timer: BusyWaitTimer = timer
        self.loggerDetails: LoggerDetails = loggerDetails
        self.segmentService: SegmentService = segmentService

    def getSegmentService(self):
        return self.segmentService

    def getLoggerDetails(self):
        return self.loggerDetails

    def changeState(self, newState):
        self.protocol.changeState(newState)

    def getPeerAddress(self):
        return self.protocol.getPeerAddress()

    def getDisconnectorAddress(self):
        return self.protocol.getDisconnectorAddress()

    def setPeerAddress(self, address):
        self.protocol.setPeerAddress(address)

    def sendTo(self, segment, address):
        self.sender.sendTo(segment, address)

    def put(self, item):
        self.eventQueue.put(item)

    def get(self):
        return self.eventQueue.get()

    def schedule(self, timeout, event):
        self.timer.schedule(timeout, self.eventQueue, event)

    def cancel(self, name):
        self.timer.cancel(name)
