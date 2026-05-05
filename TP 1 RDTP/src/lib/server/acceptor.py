from threading import Thread
from lib.logger import Logger
from lib.common.download_handler import DownloadHandler
from lib.common.upload_handler import UploadHandler
from lib.protocol.acceptor_protocol import AcceptorProtocol
from lib.protocol.enums import ClientType
from lib.server.list_clients import ListClients
from lib.utils.atomic_bool import AtomicBool


class Acceptor:
    def __init__(self, protocol: AcceptorProtocol):
        self.protocol: AcceptorProtocol = protocol
        self.running: AtomicBool = AtomicBool(True)
        self.clientHandlers: ListClients = ListClients()
        self.logger: Logger = protocol.getLogger()
        self.thread: Thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.running.get():
            try:
                newProtocol = self.protocol.accept()
                if newProtocol is None:
                    continue
                newClient = None

                if newProtocol.clientType == ClientType.DOWNLOAD:
                    newClient = UploadHandler(
                        newProtocol, self.protocol.fileManager)
                elif newProtocol.clientType == ClientType.UPLOAD:
                    newClient = DownloadHandler(
                        newProtocol, self.protocol.fileManager)
                else:
                    continue

                self.clientHandlers.addClient(newClient)
                newClient.start()
            except Exception as e:
                if self.running.get():
                    self.logger.error(f"Exception occurred: {e}")
                else:
                    break
            finally:
                self._reap()
        self._clear()

    def stop(self):
        self.running.set(False)
        self.protocol.close()
        self.thread.join()

    def _reap(self):
        self.clientHandlers.reap()

    def _clear(self):
        self.clientHandlers.clear()
