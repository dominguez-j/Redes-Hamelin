from lib.event.event import Event


class AbortEvent(Event):
    def __init__(self):
        super().__init__("ABORT")
