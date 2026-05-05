from lib.protocol.acceptor_protocol import AcceptorProtocol
from lib.protocol.disconnector_protocol import DisconnectorProtocol
from lib.protocol.socket import Socket
from lib.file_manager.file_manager import FileManager
from lib.server.acceptor import Acceptor
from lib.server.disconnector import Disconnector
from lib.common.definitions import Address, LoggerDetails
from lib.utils.atomic_map import AtomicMap
from lib.protocol.protocol import Protocol
from queue import Queue


class Server:
    def __init__(self, addr: Address, loggerDetails: LoggerDetails, dirPath: str):
        self.protocols: AtomicMap[Address,
                                  tuple[Queue, Protocol]] = AtomicMap()

        acceptorProtocol = AcceptorProtocol(Socket(
            addr[0], addr[1]), self.protocols, FileManager(dirPath, loggerDetails), loggerDetails)
        self.acceptor: Acceptor = Acceptor(acceptorProtocol)

        disconnectorProtocol = DisconnectorProtocol(
            Socket(addr[0], addr[1] + 1), self.protocols, loggerDetails)
        self.disconnector: Disconnector = Disconnector(disconnectorProtocol)
        self._run()

    def _run(self):
        while True:
            print("Press 'q' to quit.")
            exit = input()
            if exit == 'q':
                break

        self.disconnector.stop()
        self.acceptor.stop()
