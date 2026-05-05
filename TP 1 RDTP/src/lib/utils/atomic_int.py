import threading


class AtomicInt:
    def __init__(self):
        self.counter = 1
        self._lock = threading.Lock()

    def equals(self, num: int):
        with self._lock:
            return self.counter == num

    def get(self):
        with self._lock:
            return self.counter

    def inc(self):
        with self._lock:
            self.counter += 1
            return self.counter

    def dec(self):
        with self._lock:
            self.counter -= 1
            return self.counter
