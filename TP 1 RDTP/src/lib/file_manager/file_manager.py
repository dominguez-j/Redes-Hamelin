import os
import threading
from .file_writer import FileWriter
from .file_reader import FileReader
from lib.utils.atomic_int import AtomicInt
from lib.common.definitions import LoggerDetails
from lib.logger import Logger


class FileManager():
    def __init__(self, filePath: str, loggerDetails: LoggerDetails):
        self._filePath = os.path.normpath(filePath)
        self.loggerDetails: LoggerDetails = loggerDetails
        self.logger: Logger = Logger("[FileManager]", *loggerDetails)

        if not os.path.exists(self._filePath):
            os.makedirs(self._filePath)
            self.logger.info(f"Created directory '{self._filePath}'.")

        self._lock = threading.Lock()
        self._activeFiles: dict[str, FileWriter] = {}
        self._readersCounter: dict[str, AtomicInt] = {}
        self._readingFiles: dict[str, FileReader] = {}

    def fileExists(self, fileName: str) -> bool:
        return os.path.exists(os.path.normpath(os.path.join(self._filePath, fileName)))

    def openReader(self, fileName: str) -> FileReader:
        fileName = os.path.basename(fileName)
        path = os.path.normpath(os.path.join(self._filePath, fileName))
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"[DEBUG FILE MANAGER] '{fileName}' no existe")
        with self._lock:
            if fileName in self._activeFiles:
                raise FileExistsError(
                    f"[DEBUG FILE MANAGER] '{fileName} aun no está escrito por completo'")
            if fileName not in self._readingFiles:
                reader = FileReader(path, self.loggerDetails)
                self._readingFiles[fileName] = reader
                self._readersCounter[fileName] = AtomicInt()
            else:
                self._readersCounter[fileName].inc()
            return self._readingFiles[fileName]

    def openWriter(self, fileName: str, fileSize: int) -> FileWriter:
        fileName = os.path.basename(fileName)
        path = os.path.normpath(os.path.join(self._filePath, fileName))
        with self._lock:
            if fileName in self._activeFiles:
                raise ValueError(
                    f"[DEBUG FILE MANAGER] '{fileName}' ya está siendo escrito")
            if fileName in self._readingFiles:
                raise FileExistsError(
                    f"[DEBUG FILE MANAGER] '{fileName} ya está siendo leído")
            writer = FileWriter(path, fileSize, self.loggerDetails)
            self._activeFiles[fileName] = writer
            return writer

    def _getListActiveFiles(self) -> list[str]:
        with self._lock:
            return list(self._activeFiles.keys())

    def release(self, fileName: str):
        with self._lock:
            if fileName in self._readingFiles:
                if self._readersCounter[fileName].equals(1):
                    del self._readingFiles[fileName]
                    del self._readersCounter[fileName]
                else:
                    self._readersCounter[fileName].dec()

            if fileName in self._activeFiles:
                writer = self._activeFiles[fileName]
                try:
                    writer.close()
                finally:
                    del self._activeFiles[fileName]

    def checkRWOpened(self, fileName: str):
        with self._lock:
            if fileName in self._activeFiles:
                raise ValueError(
                    f"[DEBUG FILE MANAGER] '{fileName}' ya está siendo escrito"
                )
            if fileName in self._readingFiles:
                raise FileExistsError(
                    f"[DEBUG FILE MANAGER] '{fileName} ya está siendo leído"
                )

    def _normalizeFileName(self, fileName: str) -> str:
        return os.path.basename(fileName)

    def releaseForReader(self, fileName: str):
        fileName = self._normalizeFileName(fileName)

        with self._lock:
            self.logger.debug("--------------FILES BEING READ BEFORE RELEASE:")
            for name, counter in self._readersCounter.items():
                self.logger.debug(f"  - {name}: {counter.get()} reader(s)")
            self.logger.debug("---------------------------------------------")

            if fileName not in self._readersCounter:
                self.logger.debug(
                    f"releaseReader('{fileName}') ignored: file was not registered as being read"
                )
                return

            new_value = self._readersCounter[fileName].dec()

            if new_value <= 0:
                del self._readersCounter[fileName]
                del self._readingFiles[fileName]
                self.logger.debug(f"Removed '{fileName}' from readers map")
            else:
                self.logger.debug(
                    f"Reader count for '{fileName}' decremented to {new_value}"
                )

            self.logger.debug("--------------FILES BEING READ AFTER RELEASE:")
            for name, counter in self._readersCounter.items():
                self.logger.debug(f"  - {name}: {counter.get()} reader(s)")
            self.logger.debug("--------------------------------------------")

    def releaseForWriter(self, fileName: str) -> None:
        fileName = self._normalizeFileName(fileName)

        with self._lock:
            writer = self._activeFiles.pop(fileName, None)

            if writer is None:
                self.logger.debug(
                    f"releaseWriter ignored: "
                    f"'{fileName}' was not being written"
                )
                return

            try:
                writer.close()
            finally:
                self.logger.debug(f"Writer released. file='{fileName}'")

    def _buildPath(self, fileName: str) -> str:
        fileName = self._normalizeFileName(fileName)
        return os.path.normpath(os.path.join(self._filePath, fileName))

    # Checks if file exists and is not being written, then returns its size. Otherwise, raises an error.
    # this could replace the uses of OpenReader to check allways the fileSize
    def getFileSize(self, fileName: str) -> int:
        fileName = self._normalizeFileName(fileName)
        path = self._buildPath(fileName)

        with self._lock:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"[DEBUG FILE MANAGER] '{fileName}' no existe")

            if fileName in self._activeFiles:
                raise FileExistsError(
                    f"[DEBUG FILE MANAGER] '{fileName}' aún está siendo escrito"
                )

            return os.path.getsize(path)
