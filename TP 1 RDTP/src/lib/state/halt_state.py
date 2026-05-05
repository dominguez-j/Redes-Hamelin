from lib.state.protocol_state import ProtocolState


class HaltState(ProtocolState):
    def __init__(self):
        pass

    def isHalt(self):
        return True
