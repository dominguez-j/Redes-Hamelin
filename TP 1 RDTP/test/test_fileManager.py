import os
import unittest
import tempfile
import threading
from lib.file_manager.file_manager import FileManager


class TestFileManager(unittest.TestCase):

    def setUp(self):
        self.testDir = tempfile.TemporaryDirectory()
        self.testPath = self.testDir.name
        self.loggerDetails = (True, False)
        self.fileManager = FileManager(self.testPath, self.loggerDetails)

    def tearDown(self):
        self.testDir.cleanup()

    def testUploadAndRelease(self):
        _ = self.fileManager.openWriter("test.bin", 100)
        self.assertIn("test.bin", self.fileManager._getListActiveFiles())

        self.fileManager.release("test.bin")
        self.assertNotIn("test.bin", self.fileManager._getListActiveFiles())

    def testOpenDuplicateWriterRaisesError(self):
        self.fileManager.openWriter("test.bin", 100)
        with self.assertRaises(ValueError):
            self.fileManager.openWriter("test.bin", 100)
        self.fileManager.release("test.bin")

    def testOpenReaderFileExists(self):
        filename = "exists.txt"
        with open(os.path.join(self.testPath, filename), "w") as f:
            f.write("Test Content")
        reader_1 = self.fileManager.openReader("exists.txt")
        reader_2 = self.fileManager.openReader("exists.txt")
        self.assertIsNotNone(reader_1)
        self.assertIsNotNone(reader_2)

    def testOpenReaderNotFoundRaisesError(self):
        with self.assertRaises(FileNotFoundError):
            self.fileManager.openReader("test_not_exists.txt")

    def testConcurrentReaders(self):
        filename = "concurrent.txt"
        filepath = os.path.join(self.testPath, filename)

        chunkSize = 1024
        numThreads = 10

        with open(filepath, "wb") as f:
            f.write(os.urandom(chunkSize * numThreads))

        barrier = threading.Barrier(numThreads)
        readers = []
        results = []
        errors = []

        def open_reader():
            try:
                reader = self.fileManager.openReader(filename)
                barrier.wait()

                data = reader.readChunk(0, chunkSize)
                readers.append(reader)
                results.append(data)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=open_reader) for _ in range(numThreads)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(readers), numThreads)
        self.assertEqual(len(errors), 0)
        for data in results:
            self.assertEqual(len(data), chunkSize)


if __name__ == '__main__':
    unittest.main()
