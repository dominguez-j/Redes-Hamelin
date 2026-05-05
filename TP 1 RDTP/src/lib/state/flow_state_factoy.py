from lib.state.flow_state import FlowState
from lib.state.protocol_state import ProtocolState
from lib.state.state_context import StateContext
from lib.protocol.enums import ProtocolType
from lib.common.definitions import FileDetails


class FlowStateFactory:
    @staticmethod
    def create(ctx: StateContext, fileDetails: FileDetails, baseNumber: int) -> ProtocolState:
        match ctx.protocol.getProtocolType():
            case ProtocolType.STOP_AND_WAIT:
                return FlowState(ctx, fileDetails, baseNumber, 1, 1)
            case ProtocolType.SELECTIVE_REPEAT:
                return FlowState(ctx, fileDetails, baseNumber, 20, 20)
            case _:
                raise RuntimeError("Invalid protocol type")
