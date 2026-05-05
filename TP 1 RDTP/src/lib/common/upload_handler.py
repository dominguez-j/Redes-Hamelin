from typing import override
from lib.protocol.protocol import Protocol
from lib.file_manager.file_manager import FileManager
from lib.common.client_handler import ClientHandler


class UploadHandler(ClientHandler):
    def __init__(self, protocol: Protocol, fileManager: FileManager):
        super().__init__(protocol, fileManager, self.run)

    @override
    def run(self):
        self.protocol.sendFile(self.fileManager)
        self.is_alive.set(False)
