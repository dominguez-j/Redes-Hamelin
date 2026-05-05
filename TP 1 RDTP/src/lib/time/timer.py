from queue import Queue
import threading
import time
from lib.common.definitions import LoggerDetails
from lib.utils.list import List
from lib.utils.atomic_bool import AtomicBool
from lib.logger import Logger


class Timer:
    def __init__(self, loggerDetails: LoggerDetails):
        self.lock = threading.Lock()
        self.logger = Logger("TimerLogger", *loggerDetails)
        self.callbacks = List()
        self.isRunning = AtomicBool(True)
        self.event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def pickNextDeadline(self):
        with self.lock:
            self.logger.debug("se tomó el lock en `pickNextDeadline`")
            if self.callbacks.isEmpty():
                return None
            nextDeadline = max(0, self.callbacks.get(0)[0] - time.monotonic())
            self.logger.debug(f"Tiempo de espera del timeout: {nextDeadline}")
            return nextDeadline

    def printPuts(self, item):
        item[1].put(0)
        self.logger.debug(f"Se notificó a {item[2]}")

    def updateDeadlines(self):
        now = time.monotonic()
        with self.lock:
            self.logger.debug("se tomó el lock en `updateDeadlines`")
            self.callbacks.forEach(
                lambda x: self.printPuts(x) if x[0] <= now else None)
            self.callbacks.filter(lambda x: x[0] > now)
            self.logger.debug("Callbacks: %s", self.callbacks.__str__())

    def getNotifier(self):
        return Queue()

    def schedule(self, delayInSeconds: float, q: Queue, name: str):
        self.logger.debug(f"Añadiendo timer {name}")
        deadline = time.monotonic() + delayInSeconds
        with self.lock:
            self.logger.debug(f"{name} tomó el lock en `schedule`")
            self.callbacks.insertSorted(
                (deadline, q, name), lambda a, b: a[0] > b[0])
            self.event.set()

    def stop(self):
        self.logger.debug("Deteniendo")
        self.isRunning.set(False)
        self.event.set()
        self.thread.join()

    def run(self):
        while self.isRunning.get():
            timeout = self.pickNextDeadline()
            self.event.wait(timeout)
            self.event.clear()
            self.updateDeadlines()
