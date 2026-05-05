from lib.common.download_handler import DownloadHandler
from lib.common.upload_handler import UploadHandler
from lib.common.constants import DOWNLOAD, UPLOAD, SW
from lib.common.definitions import Address, LoggerDetails
from lib.protocol.connector_protocol import ConnectorProtocol
from lib.protocol.socket import Socket
from lib.protocol.enums import ClientType, ProtocolType
from lib.file_manager.file_manager import FileManager
import time


class Client:
    def __init__(
        self,
        addr: Address,
        loggerDetails: LoggerDetails,
        dir_path: str,
        fileName: str,
        mode: str,
        protocolType: str,
    ):
        ctype = ClientType.DOWNLOAD if mode == DOWNLOAD else ClientType.UPLOAD
        ptype = ProtocolType.STOP_AND_WAIT if protocolType == SW else ProtocolType.SELECTIVE_REPEAT
        fileManager = FileManager(dir_path, loggerDetails)
        socket = Socket()
        socket.setTimeout(1)
        protocol = ConnectorProtocol(
            socket, ctype, ptype, fileName, loggerDetails).connect(addr)

        if mode == DOWNLOAD:
            self.client = DownloadHandler(protocol, fileManager)
        elif mode == UPLOAD:
            self.client = UploadHandler(protocol, fileManager)
        else:
            raise ValueError("Invalid mode. Must be 'download' or 'upload'.")

        t0 = time.monotonic()
        self.client.start()
        self.client.stop()
        print("[CLIENT] ELAPSED: ", time.monotonic() - t0)
