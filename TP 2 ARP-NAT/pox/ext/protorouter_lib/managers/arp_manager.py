"""
ArpManager

Encapsula todo lo relacionado a ARP que antes estaba sueltо en ProtoRouter:

  - self.arp_table       -> tabla IP -> ArpEntry
  - self.pending_packets -> paquetes que están esperando que se resuelva
                             una MAC vía ARP

La idea es que ProtoRouter  no manipule estos diccionarios directamente.
Le "pregunta" al manager (knows, lookup, learn, queue_pending,
pop_pending) y el manager responde con la información o con un resultado
simple (True/False, una entrada, una lista). 
"""

from pox.lib.addresses import EthAddr, IPAddr


from protorouter_lib.constants import PRIVATE, PUBLIC
from protorouter_lib.models.arp_entry import ArpEntry

class ArpManager:
    def __init__(self, private_network: IPAddr, private_mask: int):
        self._private_network = private_network
        self._private_mask = private_mask

        self._table: dict = {}  # IPAddr -> ArpEntry
        self._pending: dict = {}  # IPAddr -> list[PendingPacket]


    def knows(self, ip_addr) -> bool:
        return IPAddr(ip_addr) in self._table

    def lookup(self, ip_addr):
        return self._table.get(IPAddr(ip_addr))

    def all_entries(self) -> dict:
        return dict(self._table)
    
    def evict_stale_entries(self):

        expired_entries = [
            (ip, entry)
            for ip, entry in self._table.items()
            if entry.is_stale()
        ]

        for ip, _entry in expired_entries:
            self._table.pop(ip, None)

        return expired_entries
    
    def learn(self, ip_addr, mac_addr, in_port):
        ip_addr = IPAddr(ip_addr)

        port_type = (
            PRIVATE
            if ip_addr.inNetwork(self._private_network, self._private_mask)
            else PUBLIC
        )

        existing = self._table.get(ip_addr)

        if existing is not None:
            existing.update(EthAddr(mac_addr), in_port, port_type)
            return existing, False

        entry = ArpEntry(EthAddr(mac_addr), in_port, port_type)
        self._table[ip_addr] = entry

        print("ARP LEARN - nueva entrada:")
        print("  IP:", ip_addr)
        print("  MAC:", mac_addr)
        print("  Puerto:", in_port)
        print("  Tipo:", port_type)

        return entry, True

    def queue_pending(self, ip_addr, pending_packet) -> bool:
        ip_addr = IPAddr(ip_addr)
        is_first_for_this_ip = ip_addr not in self._pending
        self._pending.setdefault(ip_addr, []).append(pending_packet)
        return is_first_for_this_ip

    def pop_pending(self, ip_addr) -> list:
        return self._pending.pop(IPAddr(ip_addr), [])

    def has_pending(self, ip_addr) -> bool:
        return IPAddr(ip_addr) in self._pending
    
    def debug_snapshot(self):
        return [
            {
                "ip": str(ip),
                "mac": str(entry.mac),
                "openflow_port": entry.switch_openflow_port,
                "type": entry.port_type,
            }
            for ip, entry in self._table.items()
        ]

