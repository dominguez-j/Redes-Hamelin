import threading
from typing import Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class AtomicMap(Generic[T, U]):
    def __init__(self):
        self.lock = threading.Lock()
        self.map = {}

    def callOnMap(self, fun):
        with self.lock:
            return fun(self.map)

    def get(self, key):
        with self.lock:
            return self.map.get(key)

    def __getitem__(self, key):
        with self.lock:
            return self.map.get(key)

    def set(self, key, value):
        with self.lock:
            self.map[key] = value

    def __setitem__(self, key, value):
        with self.lock:
            self.map[key] = value

    def remove(self, key):
        with self.lock:
            del self.map[key]
