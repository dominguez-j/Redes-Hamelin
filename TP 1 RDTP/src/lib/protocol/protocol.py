from lib.file_manager.file_manager import FileManager
from lib.utils.atomic_bool import AtomicBool
from lib.protocol.sender import Sender
from lib.protocol.receiver import Receiver
from lib.protocol.enums import ClientType, ProtocolType
from lib.common.definitions import Address


class Protocol:
    def __init__(
            self,
            peerAddress: Address,
            disconnectorAddress: Address,
            sender: Sender,
            receiver: Receiver,
            cType: ClientType,
            pType: ProtocolType):
        self.initialState = None
        self.isRunning: AtomicBool = AtomicBool(True)
        self.peerAddress: Address = peerAddress
        self.disconnectorAddress: Address = disconnectorAddress
        self.sender: Sender = sender
        self.receiver: Receiver = receiver
        self.clientType: ClientType = cType
        self.protocolType = pType

    def isHalt(self):
        return self.state.isHalt() if self.state is not None else True

    def setPeerAddress(self, address: Address):
        self.peerAddress = address

    def getPeerAddress(self):
        return self.peerAddress

    def getDisconnectorAddress(self):
        return self.disconnectorAddress

    def changeState(self, newState):
        self.state = newState

    def sendFile(self, fileManager: FileManager):
        while self.isRunning.get():
            if not self.state.isHalt():
                self.state.sendFile(fileManager)
            else:
                self.isRunning.set(False)
        self.receiver.stop()

    def downloadFile(self, fileManager: FileManager):
        while self.isRunning.get():
            if not self.state.isHalt():
                self.state.downloadFile(fileManager)
            else:
                self.isRunning.set(False)
        self.receiver.stop()

    def getProtocolType(self):
        return self.protocolType
