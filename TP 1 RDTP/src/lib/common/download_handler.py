from typing import override
from lib.file_manager.file_manager import FileManager
from lib.protocol.protocol import Protocol
from lib.common.client_handler import ClientHandler


class DownloadHandler(ClientHandler):
    def __init__(self, protocol: Protocol, fileManager: FileManager):
        super().__init__(protocol, fileManager, self.run)

    @override
    def run(self):
        self.protocol.downloadFile(self.fileManager)
        self.is_alive.set(False)
