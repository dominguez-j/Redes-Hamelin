# Import some POX stuff

from pox.lib.recoco import Timer

from pox.core import core  
from pox.lib.addresses import EthAddr, IPAddr  
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet
from protorouter_lib.constants import (
    INITIAL_ASSIGNED_PORT,
    PROTO_TCP,
    PROTO_UDP,
    PROTO_IP_NUMBER,
    IP_NUMBER_TO_PROTO,
)
import pox.openflow.libopenflow_01 as of
from protorouter_lib.managers.arp_manager import ArpManager
from protorouter_lib.managers.nat_manager import NatManager
from protorouter_lib.models.pending_packet import PendingPacket
from protorouter_lib.openflow_sender import OpenFlowSender
from collections import namedtuple


log = core.getLogger()
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def log_color(color, msg):
    log.info(f"{color}{msg}{RESET}")


PRIVATE_SUBNET = IPAddr("192.168.1.0")  # Red interna
PRIVATE_MASK = 24  # Máscara de la red interna
PRIVATE_IP = IPAddr("192.168.1.254")  # IP del router en la red privada
PUBLIC_IP = IPAddr("200.0.0.254")  # IP del router en la red pública
PUBLIC_MAC = EthAddr("00:00:00:aa:aa:aa")  # MAC del router hacia la red pública
PRIVATE_MAC = EthAddr("00:00:00:bb:bb:bb")  # MAC del router hacia la red privada
PUBLIC_PORT = 1  # Puerto del switch conectado a la red pública

H1_MAC = EthAddr(
    "00:00:00:00:00:01"
)  

# Datos de un flujo saliente, parseados una sola vez del paquete IP.
FlowInfo = namedtuple(
    "FlowInfo",
    [
        "protocol",
        "host_private_ip",
        "host_private_port",
        "host_private_mac",
        "private_openflow_port",
        "host_public_ip",
        "host_public_port",
    ],
)

class ProtoRouter(object):
    def __init__(self, connection):
        self.nat_private_net = PRIVATE_SUBNET
        self.nat_private_mask = PRIVATE_MASK
        self.nat_private_ip = PRIVATE_IP
        self.nat_public_ip = PUBLIC_IP
        self.nat_private_mac = PRIVATE_MAC
        self.nat_public_mac = PUBLIC_MAC
        self.arp_manager = ArpManager(self.nat_private_net, self.nat_private_mask)
        self.nat_manager = NatManager(INITIAL_ASSIGNED_PORT)

        self.openflow_ports: set = set()
        self.global_counter: int = 1 
        self.connection = connection
        connection.addListeners(self)
        self.openflow_sender = OpenFlowSender(connection=self.connection)

        Timer(5, self.cleanup_arp_table, recurring=True)

    def cleanup_arp_table(self):
        expired_arp_entries = self.arp_manager.evict_stale_entries()

        if expired_arp_entries:
            for ip, entry in expired_arp_entries:
                log_color(
                    CYAN,
                    f"ARP entry expired and removed: "
                    f"{ip} -> {entry.mac} | "
                    f"port={entry.switch_openflow_port} | "
                    f"type={entry.port_type}",
                )

            log_color(
                CYAN,
                f"Tabla ARP después de limpiar "
                f"({len(self.arp_manager.debug_snapshot())} entrada/s): "
                f"{self.arp_manager.debug_snapshot()}",
            )

    def _handle_PacketIn(self, event):
        log_color(RED, f"_handle_PacketIn has been called {self.global_counter} times")
        self.global_counter += 1

        packet = event.parsed

        if not packet.parsed:
            log.warning(
                "[DROP] PacketIn con trama no reconocida. POX no pudo decodificar el paquete."
            )
            return

        if packet.type == ethernet.IP_TYPE:
            self.handle_ip(event)

        elif packet.type == ethernet.ARP_TYPE:
            self.handle_arp_type(event)

        else:
            log_color(RED, f"Packet ignored: protocol received: {packet.type}.")

    def handle_arp_type(self, event):
        packet = event.parsed
        arp_packet = packet.payload

        if arp_packet.opcode == arp.REQUEST:
            self.handle_packet_arp_request(event)

        elif arp_packet.opcode == arp.REPLY:
            self.handle_packet_arp_reply(event)

    def handle_packet_arp_reply(self, event):
        log_color(YELLOW, "Handling an ARP Reply")
        packet = event.parsed
        arp_packet = packet.payload

        host_public_ip = arp_packet.protosrc
        host_public_mac = arp_packet.hwsrc
        public_openflow_port = event.port

        self.learn_arp_entry(public_openflow_port, host_public_ip, host_public_mac)

        pending_list = self.arp_manager.pop_pending(host_public_ip)

        if not pending_list:
            log_color(YELLOW, f"No pending packets for {host_public_ip}")
            return

        for pending_packet in pending_list:
            nat_entry = pending_packet.nat_entry

            if nat_entry is None:
                log_color(RED, "[ERROR] Pending packet without NAT entry")
                continue

            self.complete_and_forward(
                nat_entry, host_public_mac, public_openflow_port, pending_packet.raw_packet
            )

    def handle_packet_arp_request(self, event):
        log_color(YELLOW, "Handling an ARP Request")
        packet = event.parsed
        arp_packet = packet.payload
        in_port = event.port
        addr_asked = packet.payload.protodst

        self.learn_arp_entry(in_port, packet.payload.protosrc, packet.payload.hwsrc)

        if addr_asked == self.nat_private_ip:
            self.openflow_sender.make_an_arp_reply(
                arp_packet, self.nat_private_mac, addr_asked, in_port
            )
            return

        elif addr_asked == self.nat_public_ip:
            self.openflow_sender.make_an_arp_reply(
                arp_packet, self.nat_public_mac, addr_asked, in_port
            )
            return

        log_color(
            YELLOW,
            f"ARP request ignored: {arp_packet.protosrc} asked for {addr_asked}, "
            f"This IP does not belong to Switch NAT",
        )

    def learn_arp_entry(self, in_port, ip_addr, mac_addr):
        entry, is_new = self.arp_manager.learn(ip_addr, mac_addr, in_port)

        if is_new:
            log_color(
                CYAN,
                f"ARP learned: {IPAddr(ip_addr)} -> {entry.mac} | port={in_port} | type={entry.port_type}",
            )
        else:
            log_color(
                CYAN,
                f"ARP already exists: {IPAddr(ip_addr)} -> {entry.mac} | port={in_port} ",
            )

    def handle_ip(self, event):
        packet = event.parsed
        ip_pkt = packet.payload
        in_port = event.port
        ip_dst = ip_pkt.dstip

        if ip_pkt.protocol not in (ip_pkt.TCP_PROTOCOL, ip_pkt.UDP_PROTOCOL):
            log_color(
                YELLOW,
                f"[DROP] Protocolo IP no soportado: {ip_pkt.protocol} "
                f"({ip_pkt.srcip} → {ip_pkt.dstip})",
            )
            return

        log_color(
            YELLOW,
            f"RECIBIDO: {ip_pkt.srcip} → {ip_pkt.dstip} | "
            f"MAC: {packet.src} → {packet.dst} | In Port: {in_port}",
        )

        if ip_pkt.srcip.inNetwork(PRIVATE_SUBNET, PRIVATE_MASK):
            log_color(
                GREEN,
                f"MATCH: {ip_pkt.srcip} belongs to private network {PRIVATE_SUBNET}/{PRIVATE_MASK}",
            )

            if not self.arp_manager.knows(ip_dst):
                self.ask_for_mac_to_public_host(event)
                return

            self.forward_with_known_mac(event)

        else:
            log_color(
                RED,
                f"NO MATCH: {ip_pkt.srcip} no pertenece a {PRIVATE_SUBNET}/{PRIVATE_MASK}",
            )

    def ask_for_mac_to_public_host(self, event):
        packet = event.parsed
        ip_packet = packet.payload
        target_ip = ip_packet.dstip
        if IPAddr(target_ip).inNetwork(self.nat_private_net, self.nat_private_mask):
            log_color(RED, "[ERROR] MAC address Searchs just for private hosts")
            return

        flow_info = self.extract_flow_info(packet, event.port)
        if flow_info is None:
            return

        nat_entry, is_new = self.nat_manager.get_or_create_outgoing_entry(
            flow_info.protocol,
            flow_info.host_private_ip,
            flow_info.host_private_port,
            flow_info.host_private_mac,
            flow_info.private_openflow_port,
            flow_info.host_public_ip,
            flow_info.host_public_port,
        )

        snapshot = self.nat_manager.debug_snapshot()
        log_color(CYAN, f"Tabla NAT ({len(snapshot)} entrada/s): {snapshot}")

        if not is_new:
            log_color(
                YELLOW,
                f"Paquete repetido para un flujo ya en curso (estado={nat_entry.state}), se descarta",
            )
            return

        log_color(YELLOW, f"New NAT Entry (PENDING):\n {nat_entry}\n")

        raw_packet: bytes = event.ofp.data
        pending_packet = PendingPacket(event.port, raw_packet, nat_entry)

        self.add_pending_packet(target_ip, pending_packet)

    def forward_with_known_mac(self, event):
        packet = event.parsed
        ip_packet = packet.payload
        target_ip = ip_packet.dstip

        arp_entry = self.arp_manager.lookup(target_ip)
        if arp_entry is None:
            self.ask_for_mac_to_public_host(event)
            return

        flow_info = self.extract_flow_info(packet, event.port)
        if flow_info is None:
            return

        nat_entry, is_new = self.nat_manager.get_or_create_outgoing_entry(
            flow_info.protocol,
            flow_info.host_private_ip,
            flow_info.host_private_port,
            flow_info.host_private_mac,
            flow_info.private_openflow_port,
            flow_info.host_public_ip,
            flow_info.host_public_port,
        )

        if not is_new:
            log_color(
                YELLOW,
                f"Paquete con MAC ya conocida pero flujo ya en curso (estado={nat_entry.state}), se descarta",
            )
            return

        raw_packet: bytes = event.ofp.data
        self.complete_and_forward(
            nat_entry, arp_entry.mac, arp_entry.switch_openflow_port, raw_packet
        )

    def add_pending_packet(self, target_ip, pending_packet):
        is_first_for_this_ip = self.arp_manager.queue_pending(
            target_ip, pending_packet
        )

        if is_first_for_this_ip:
            self.openflow_sender.make_an_arp_request(
                target_ip, PUBLIC_PORT, self.nat_public_mac, self.nat_public_ip
            )

    def extract_flow_info(self, eth_packet, in_port):
        ip_packet = eth_packet.payload
        udp_packet = eth_packet.find(PROTO_UDP)
        tcp_packet = eth_packet.find(PROTO_TCP)

        if udp_packet is not None:
            protocol = PROTO_UDP
            transport_packet = udp_packet
        elif tcp_packet is not None:
            protocol = PROTO_TCP
            transport_packet = tcp_packet
        else:
            return None

        host_private_ip = ip_packet.srcip
        if not IPAddr(host_private_ip).inNetwork(
            self.nat_private_net, self.nat_private_mask
        ):
            return None

        return FlowInfo(
            protocol=protocol,
            host_private_ip=host_private_ip,
            host_private_port=transport_packet.srcport,
            host_private_mac=eth_packet.src,
            private_openflow_port=in_port,
            host_public_ip=ip_packet.dstip,
            host_public_port=transport_packet.dstport,
        )

    def install_flows(self, nat_entry):
        ip_proto = PROTO_IP_NUMBER.get(nat_entry.protocol)
        if ip_proto is None:
            log_color(
                RED,
                f"[ERROR] Protocolo desconocido para instalar flujo: {nat_entry.protocol}",
            )
            return

        # Instalar Flujo Saliente
        fm = of.ofp_flow_mod()
        fm.idle_timeout = nat_entry.idle_timeout
        fm.flags = of.OFPFF_SEND_FLOW_REM

        # Filtro (Saliente)
        fm.match.dl_type = 0x800  # IPv4
        fm.match.in_port = nat_entry.private_openflow_port
        fm.match.nw_proto = ip_proto
        fm.match.nw_src = nat_entry.host_private_ip
        fm.match.nw_dst = nat_entry.host_public_ip
        fm.match.tp_src = nat_entry.host_private_port
        fm.match.tp_dst = nat_entry.host_public_port

        # Acción (Saliente)
        fm.actions.append(of.ofp_action_dl_addr.set_src(self.nat_public_mac))
        fm.actions.append(of.ofp_action_dl_addr.set_dst(nat_entry.host_public_mac))
        fm.actions.append(of.ofp_action_nw_addr.set_src(self.nat_public_ip))
        fm.actions.append(of.ofp_action_tp_port.set_src(nat_entry.nat_public_port))
        fm.actions.append(of.ofp_action_output(port=nat_entry.public_openflow_port))
        self.connection.send(fm)

        # Instalar Flujo Entrante (para respuesta)
        fm_back = of.ofp_flow_mod()
        fm_back.idle_timeout = nat_entry.idle_timeout
        fm_back.flags = of.OFPFF_SEND_FLOW_REM

        # Filtro (Entrante)
        fm_back.match.dl_type = 0x800  # IPv4
        fm_back.match.in_port = nat_entry.public_openflow_port
        fm_back.match.nw_proto = ip_proto
        fm_back.match.nw_src = nat_entry.host_public_ip
        fm_back.match.nw_dst = self.nat_public_ip
        fm_back.match.tp_src = nat_entry.host_public_port
        fm_back.match.tp_dst = nat_entry.nat_public_port

        # Acción (Entrante)
        fm_back.actions.append(of.ofp_action_dl_addr.set_src(self.nat_private_mac))
        fm_back.actions.append(of.ofp_action_dl_addr.set_dst(nat_entry.host_private_mac))
        fm_back.actions.append(of.ofp_action_nw_addr.set_dst(nat_entry.host_private_ip))
        fm_back.actions.append(of.ofp_action_tp_port.set_dst(nat_entry.host_private_port))
        fm_back.actions.append(of.ofp_action_output(port=nat_entry.private_openflow_port))
        self.connection.send(fm_back)

        log_color(
            GREEN, f"Flujos instalados para puerto público {nat_entry.nat_public_port}"
        )

    """
        Termina de resolver una NatEntry (ya con MAC pública conocida),
        instala sus flujos y reenvía el paquete que la disparó — el
        equivalente al "Reenviar paquete actual" del bloque base, pero
        usando openflow_sender.forward_of_data (que ya traduce IP/puerto,
        no solo MAC)
    """
    def complete_and_forward(self, nat_entry, host_public_mac, public_openflow_port, raw_packet):
        self.nat_manager.mark_installed(nat_entry, host_public_mac, public_openflow_port)
        self.install_flows(nat_entry)

        log_color(GREEN, f"NAT entry completed:\n{nat_entry}")

        self.openflow_sender.forward_of_data(
            raw_packet,
            self.nat_public_mac,
            self.nat_public_ip,
            nat_entry.nat_public_port,
            nat_entry.public_openflow_port,
            nat_entry.host_public_mac,
            nat_entry.host_public_ip,
            nat_entry.host_public_port,
            nat_entry.host_private_ip,
            nat_entry.host_private_port,
        )
    
    def _handle_FlowRemoved(self, event):
        match = event.ofp.match

        if match.nw_dst == self.nat_public_ip:
            nat_public_port = match.tp_dst
            self.nat_manager.handle_flow_removed_incoming(nat_public_port)
            log_color(
                YELLOW, f"Flujo entrante removido por el switch (puerto público {nat_public_port})"
            )
        else:
            protocol = IP_NUMBER_TO_PROTO.get(match.nw_proto)
            if protocol is None:
                return
            self.nat_manager.handle_flow_removed_outgoing(
                protocol, match.nw_src, match.tp_src, match.nw_dst, match.tp_dst
            )
            log_color(
                YELLOW,
                f"Flujo saliente removido por el switch ({match.nw_src}:{match.tp_src} -> {match.nw_dst}:{match.tp_dst})",
            )


def launch():
    
    def start_switch(event):
        log_color(YELLOW, f"Iniciando ProtoRouter para Switch {event.connection.dpid}")
        ProtoRouter(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)