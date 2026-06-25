"""
NatManager

Por ahora sólo se extrajo de ProtoRouter la asignación de puertos
públicos (lo que antes era self.next_nat_public_port / self.assigned_ports),
para que esa lógica quede en un solo lugar.
La ideas es que aca tambien esten los metodos de pregutna y respuesta tambien.
.
"""

from protorouter_lib.models.nat_entry import NatEntry
from protorouter_lib.constants import STATE_INSTALLED


class NatManager:
    def __init__(self, initial_port: int):
        self._next_port = initial_port
        self._free_ports: list = []  # puertos liberados, listos para reusar
        self._entries: dict = {}  # nat_public_port -> NatEntry

    def get_or_create_outgoing_entry(
        self,
        protocol,
        host_private_ip,
        host_private_port,
        host_private_mac,
        private_openflow_port,
        host_public_ip,
        host_public_port,
    ):
        self.evict_stale_entries()

        existing = self._find_outgoing(
            protocol, host_private_ip, host_private_port, host_public_ip, host_public_port
        )
        if existing is not None:
            return existing, False

        nat_public_port = self._assign_public_port()
        entry = NatEntry(
            protocol,
            host_private_ip,
            host_private_port,
            host_private_mac,
            private_openflow_port,
            nat_public_port,
            host_public_ip,
            host_public_port,
            None, 
            None, 
        )
        self._entries[nat_public_port] = entry
        return entry, True

    def lookup_by_incoming(self, nat_public_port):
        self.evict_stale_entries()
        return self._entries.get(nat_public_port)

    def mark_installed(self, entry, host_public_mac, public_openflow_port):
        entry.host_public_mac = host_public_mac
        entry.public_openflow_port = public_openflow_port
        entry.state = STATE_INSTALLED
        entry.touch()


    def _find_outgoing(
        self, protocol, host_private_ip, host_private_port, host_public_ip, host_public_port
    ):
        for entry in self._entries.values():
            if (
                entry.protocol == protocol
                and entry.host_private_ip == host_private_ip
                and entry.host_private_port == host_private_port
                and entry.host_public_ip == host_public_ip
                and entry.host_public_port == host_public_port
            ):
                return entry
        return None

    def evict_stale_entries(self):
        expired_ports = [
            port for port, entry in self._entries.items() if entry.is_stale()
        ]
        for port in expired_ports:
            self._remove_entry(port)
        return expired_ports

    def _remove_entry(self, nat_public_port):
        self._entries.pop(nat_public_port, None)
        self._release_port(nat_public_port)

    def _assign_public_port(self) -> int:
        if self._free_ports:
            return self._free_ports.pop()
        port = self._next_port
        self._next_port += 1
        return port

    def _release_port(self, port: int):
        self._free_ports.append(port)

    def handle_flow_removed_outgoing(
        self, protocol, host_private_ip, host_private_port, host_public_ip, host_public_port
    ):
        entry = self._find_outgoing(
            protocol, host_private_ip, host_private_port, host_public_ip, host_public_port
        )
        if entry is None:
            return
        if entry.mark_flow_removed("outgoing"):
            self._remove_entry(entry.nat_public_port)

    def handle_flow_removed_incoming(self, nat_public_port):
        entry = self._entries.get(nat_public_port)
        if entry is None:
            return
        if entry.mark_flow_removed("incoming"):
            self._remove_entry(nat_public_port)

    def debug_snapshot(self):
        """Resumen legible de la tabla actual, para debug/CLI."""
        return [
            {
                "nat_public_port": port,
                "private": f"{entry.host_private_ip}:{entry.host_private_port}",
                "public": f"{entry.host_public_ip}:{entry.host_public_port}",
                "state": entry.state,
            }
            for port, entry in self._entries.items()
        ]