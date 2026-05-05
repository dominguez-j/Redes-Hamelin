import threading
import time
from queue import Queue

from lib.event.event import Event
from lib.logger import Logger
from lib.utils.list import List
from lib.utils.atomic_bool import AtomicBool


class BusyWaitTimer:
    def __init__(self):
        self.lock = threading.Lock()
        self.logger = Logger("BusyTimerLogger", False, False)
        self.callbacks = List()
        self.isRunning = AtomicBool(True)
        self.defaultTimeout = 0.1
        self.timeout = 0.1
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def updateDeadlines(self):
        now = time.monotonic()
        with self.lock:
            self.logger.debug("se tomó el lock en `updateDeadlines`")
            self.callbacks.forEach(lambda x: x[1].put(
                x[2]) if x[0] <= now else None)
            self.callbacks.filter(lambda x: x[0] > now)
            self.timeout = (
                min(self.timeout, self.callbacks.get(0)[0] - now)
                if not self.callbacks.isEmpty()
                else self.defaultTimeout
            )
            self.logger.debug("Callbacks: %s", self.callbacks.__str__())

    def getNotifier(self):
        return Queue()

    def schedule(
        self,
        delayInSeconds: float,
        q: Queue,
        event: Event
    ):
        deadline = time.monotonic() + delayInSeconds
        with self.lock:
            self.logger.debug(f"{event.getName()} tomó el lock en `schedule`")
            self.callbacks.insertSorted(
                (deadline, q, event), lambda a, b: a[0] > b[0]
            )
            self.timeout = min(self.timeout, delayInSeconds)

    def cancel(self, name: str):
        with self.lock:
            self.logger.debug(f"{name} tomó el lock en `cancel`")
            self.callbacks.filter(lambda x: x[2].getName() != name)

    def stop(self):
        self.logger.debug("Deteniendo")
        self.isRunning.set(False)
        self.thread.join()

    def run(self):
        while self.isRunning.get():
            time.sleep(self.timeout)
            self.updateDeadlines()
