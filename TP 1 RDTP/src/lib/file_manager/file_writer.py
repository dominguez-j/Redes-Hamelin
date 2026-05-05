import os
import threading
from lib.logger import Logger
from lib.common.definitions import LoggerDetails


class FileWriter:

    def __init__(self, filePath: str, fileSize: int, loggerDetails: LoggerDetails):
        self._filePath = filePath
        self._fileSize = fileSize
        self._lock = threading.Lock()
        self._allocate()
        self._file = open(self._filePath, "r+b")
        self.logger: Logger = Logger("[FileWriter]", *loggerDetails)

    def getFileSize(self) -> int:
        return self._fileSize

    def _allocate(self):
        path = os.path.normpath(self._filePath)
        with open(path, "wb") as f:
            f.seek(self._fileSize - 1)
            f.write(b'\0')

    def writeChunk(self, offset: int, data: bytes):
        self.logger.info(
            f"Escribir chunk a '{self._filePath}' de offset {offset} con longitud {len(data)}")
        if offset + len(data) > self._fileSize:
            raise ValueError(
                f"[DEBUG FILE UPLOAD] Supera el tamaño del archivo: "
                f"offset {offset} + data length {len(data)} > "
                f"file size {self._fileSize}")

        with self._lock:
            self._file.seek(offset)
            self._file.write(data)

    def writeBatch(self, offset: int, chunks: list[bytes]):
        totaLengthToWrite = sum(len(chunk) for chunk in chunks)
        if offset + totaLengthToWrite > self._fileSize:
            raise ValueError(
                f"[DEBUG FILE UPLOAD] Supera el tamaño del archivo: "
                f"offset {offset} + total length {totaLengthToWrite} > "
                f"file size {self._fileSize}")

        with self._lock:
            self._file.seek(offset)
            for chunk in chunks:
                self._file.write(chunk)

    def close(self):
        self.logger.info("CLOSING")
        if self._file and not self._file.closed:
            self.logger.info("FLUSING")
            self._file.flush()
            self._file.close()
