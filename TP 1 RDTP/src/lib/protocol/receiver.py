from threading import Thread
from queue import Queue
from socket import timeout
from lib.logger import Logger
from lib.utils.atomic_bool import AtomicBool
from lib.protocol.socket import Socket
from lib.event.segment_event import SegmentEvent
from lib.segment.segment import Segment
from lib.common.definitions import LoggerDetails


class Receiver:
    def __init__(self, socket: Socket, eventQueue: Queue, loggerDetails: LoggerDetails):
        self.socket: Socket = socket
        self.eventQueue: Queue = eventQueue
        self.isRunning: AtomicBool = AtomicBool(True)
        self.logger = Logger("[Receiver]", *loggerDetails)
        self.thread: Thread = Thread(target=self.start)
        self.thread.start()

    def start(self):
        while self.isRunning.get():
            try:
                segment, addr = self.socket.recvFrom(Segment.SIZE_MAX_SEG)
                if segment.calculateChecksum() != segment.getChecksum():
                    self.logger.info("Received segment with invalid checksum")
                    continue
                self.eventQueue.put(SegmentEvent(segment, addr))
            except timeout:
                continue
            except TimeoutError:
                continue
            except OSError as e:
                self.logger.error(f"Socket error: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break

    def stop(self):
        self.isRunning.set(False)
        self.thread.join()
