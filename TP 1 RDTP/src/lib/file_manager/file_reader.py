import os
import threading
from lib.logger import Logger
from lib.common.definitions import LoggerDetails


class FileReader:
    def __init__(self, filePath: str, loggerDetails: LoggerDetails):
        self._filePath = filePath
        self._file_size = os.path.getsize(filePath)
        self._lock = threading.Lock()
        self.logger: Logger = Logger("[FileReader]", *loggerDetails)

    def getFileSize(self) -> int:
        with self._lock:
            return self._file_size

    def readChunk(self, offset: int, chunkSize: int) -> bytes:
        self.logger.info(
            f"Leer chunks de '{self._filePath}' de offset {offset} con tamaño {chunkSize}")
        with self._lock:
            path = os.path.normpath(self._filePath)
            with open(path, "rb") as f:
                f.seek(offset)
                return f.read(chunkSize)

    def readBatch(self, offset: int, windowSize: int, chunkSize: int) -> list[bytes]:
        self.logger.info(
            f"Leer batch de chunks de '{self._filePath}' de offset {offset}"
            f"con window size {windowSize} y chunk size {chunkSize}")
        with self._lock:
            bytesToRead = min(windowSize * chunkSize, self._file_size - offset)
            with open(self._filePath, "rb") as f:
                f.seek(offset)
                data = f.read(bytesToRead)

            chunks = []
            for i in range(0, len(data), chunkSize):
                chunk = data[i: i + chunkSize]
                chunks.append(chunk)
            return chunks

    def getFileSizeFromFileName(self, fileName: str) -> int:
        with self._lock:
            path = os.path.normpath(os.path.join(self._filePath, fileName))
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"[DEBUG FILE READER] '{fileName}' no existe")
            return os.path.getsize(path)

    def readAllChunks(self, chunkSize: int) -> list[bytes]:
        with self._lock:
            chunks = []
            with open(self._filePath, "rb") as f:
                while True:
                    chunk = f.read(chunkSize)
                    if not chunk:
                        break
                    chunks.append(chunk)
            return chunks
