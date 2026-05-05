from threading import Thread
from lib.logger import Logger
from lib.protocol.disconnector_protocol import DisconnectorProtocol
from lib.utils.atomic_bool import AtomicBool


class Disconnector:
    def __init__(self, protocol: DisconnectorProtocol):
        self.protocol: DisconnectorProtocol = protocol
        self.running: AtomicBool = AtomicBool(True)
        self.logger: Logger = protocol.getLogger()
        self.thread: Thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        while self.running.get():
            try:
                self.protocol.disconnect()
            except Exception as e:
                if self.running.get():
                    self.logger.error(f"Exception occurred: {e}")
                    pass
                else:
                    break

    def stop(self):
        self.running.set(False)
        self.protocol.close()
        self.thread.join()
