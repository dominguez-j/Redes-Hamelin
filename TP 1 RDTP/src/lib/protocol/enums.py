from enum import Enum


class ClientType(Enum):
    UPLOAD = 0
    DOWNLOAD = 1


class ProtocolType(Enum):
    STOP_AND_WAIT = 0
    SELECTIVE_REPEAT = 1
