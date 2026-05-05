from threading import Thread
from lib.file_manager.file_manager import FileManager
from lib.utils.atomic_bool import AtomicBool
from lib.protocol.protocol import Protocol


class ClientHandler:
    def __init__(self, protocol: Protocol, fileManager: FileManager, run):
        self.protocol: Protocol = protocol
        self.fileManager: FileManager = fileManager
        self.is_alive: AtomicBool = AtomicBool(True)
        self.thread = Thread(target=run, daemon=True)

    def run(self):
        pass

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join()

    def isAlive(self) -> bool:
        return self.is_alive.get()
