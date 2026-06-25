import time


class PendingPacket:
    def __init__(self, in_port: int, raw_packet: bytes, nat_entry):
        self.in_port = in_port
        self.raw_packet = raw_packet
        self.nat_entry = nat_entry
        self.created_at = time.monotonic()
