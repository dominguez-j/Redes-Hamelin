from threading import Lock


class AtomicBool:
    def __init__(self, value=False):
        self.lock = Lock()
        self.value = value

    def get(self):
        with self.lock:
            return self.value

    def set(self, value):
        with self.lock:
            self.value = value

    def toggle(self):
        with self.lock:
            self.value = not self.value
