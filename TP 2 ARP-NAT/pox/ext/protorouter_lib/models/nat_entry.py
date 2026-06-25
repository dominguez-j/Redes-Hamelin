import time

from protorouter_lib.constants import STATE_INSTALLED, STATE_PENDING_ARP, TIME_OUT


class NatEntry:
    def __init__(
        self,
        protocol,
        host_private_ip,
        host_private_port,
        host_private_mac,
        private_openflow_port,
        nat_public_port,
        host_public_ip,
        host_public_port,
        host_public_mac,
        public_openflow_port,
    ):

        self.protocol: str = protocol

        self.host_private_ip: str = host_private_ip
        self.host_private_port: int = host_private_port
        self.host_private_mac: str = host_private_mac
        self.private_openflow_port: int = private_openflow_port

        self.nat_public_port: int = nat_public_port

        self.host_public_ip: str = host_public_ip
        self.host_public_port: int = host_public_port
        self.host_public_mac = host_public_mac
        self.public_openflow_port = public_openflow_port

        self.last_seen = time.monotonic()
        self.idle_timeout: int = TIME_OUT
        self.state: str = STATE_PENDING_ARP
        self.outgoing_flow_removed = False
        self.incoming_flow_removed = False

    def touch(self):
        self.last_seen = time.monotonic()
    
    def mark_flow_removed(self, direction: str) -> bool:
        if direction == "outgoing":
            self.outgoing_flow_removed = True
        elif direction == "incoming":
            self.incoming_flow_removed = True
        return self.outgoing_flow_removed and self.incoming_flow_removed

    def is_stale(self) -> bool:
        if self.state == STATE_INSTALLED:
            return False
        return (time.monotonic() - self.last_seen) > self.idle_timeout

    def __repr__(self):
        return (
            "NatEntry("
            f"protocol={self.protocol}, \n"
            f"private={self.host_private_ip}:{self.host_private_port}, \n"
            f"private_mac={self.host_private_mac}, \n"
            f"private_of_port={self.private_openflow_port}, \n"
            f"nat_public_port={self.nat_public_port}, \n"
            f"public={self.host_public_ip}:{self.host_public_port}, \n"
            f"public_mac={self.host_public_mac}, \n"
            f"public_of_port={self.public_openflow_port}, \n"
            f"state={self.state} \n"
            ")"
        )
