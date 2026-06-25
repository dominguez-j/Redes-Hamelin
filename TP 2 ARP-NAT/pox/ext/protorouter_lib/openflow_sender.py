import pox.openflow.libopenflow_01 as of
from pox.core import core  
from pox.lib.addresses import EthAddr, IPAddr  
from pox.lib.packet.arp import arp
from pox.lib.packet.ethernet import ethernet

from protorouter_lib.constants import (
    ETHER_BROADCAST,
    IP_ADDR_LENGTH,
    MAC_ETHER_LENGTH,
    MAC_UNKNOWN,
)

log = core.getLogger()
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def log_color(color, msg):
    log.info(f"{color}{msg}{RESET}")


class OpenFlowSender:
    def __init__(self, connection):
        self.connection = connection

    def make_an_arp_reply(self, arp_packet, mac_response, addr_response, outport):
        reply = arp()
        reply.hwtype = arp_packet.hwtype
        reply.prototype = arp_packet.prototype
        reply.hwlen = arp_packet.hwlen
        reply.protolen = arp_packet.protolen
        reply.opcode = arp.REPLY

        reply.hwsrc = EthAddr(mac_response)
        reply.hwdst = arp_packet.hwsrc
        reply.protosrc = IPAddr(addr_response)
        reply.protodst = arp_packet.protosrc

        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.dst = arp_packet.hwsrc
        ether.src = mac_response
        ether.payload = reply

        msg = of.ofp_packet_out()
        msg.data = ether.pack()
        msg.actions.append(of.ofp_action_output(port=outport))
        log_color(
            RED,
            f"Responding MAC: {reply.hwsrc} | From IP: {reply.protosrc} | To MAC: {reply.hwdst} | To IP: {reply.protodst}",
        )
        self.connection.send(msg)

    def make_an_arp_request(self, target_ip, outport, nat_public_mac, nat_public_ip):
        target_ip = IPAddr(target_ip)

        request = arp()
        request.hwtype = arp.HW_TYPE_ETHERNET
        request.prototype = arp.PROTO_TYPE_IP
        request.hwlen = MAC_ETHER_LENGTH
        request.protolen = IP_ADDR_LENGTH
        request.opcode = arp.REQUEST

        request.hwsrc = nat_public_mac
        request.hwdst = EthAddr(MAC_UNKNOWN)
        request.protosrc = nat_public_ip
        request.protodst = target_ip

        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.dst = EthAddr(ETHER_BROADCAST)
        ether.src = nat_public_mac
        ether.payload = request

        msg = of.ofp_packet_out()
        msg.data = ether.pack()
        msg.actions.append(of.ofp_action_output(port=outport))
        log_color(
            RED,
            f"Requesting MAC | From IP: {request.protosrc} | From MAC: {request.hwsrc} | To IP: {request.protodst}",
        )
        self.connection.send(msg)

    def forward_of_data(
        self,
        raw_data,
        nat_public_mac,
        nat_public_ip,
        nat_public_port,
        public_openflow_port,
        host_public_mac,
        host_public_ip,
        host_public_port,
        host_private_ip,
        host_private_port,
    ):
        msg = of.ofp_packet_out()
        msg.data = raw_data
        msg.actions.append(of.ofp_action_dl_addr.set_src(nat_public_mac))
        msg.actions.append(of.ofp_action_dl_addr.set_dst(host_public_mac))

        msg.actions.append(of.ofp_action_nw_addr.set_src(nat_public_ip))

        msg.actions.append(of.ofp_action_tp_port.set_src(nat_public_port))

        msg.actions.append(of.ofp_action_output(port=public_openflow_port))

        log_color(
            GREEN,
            f"Forwarding pending packet with NAT: "
            f"{host_private_ip}:{host_private_port} "
            f"-> {host_public_ip}:{host_public_port} "
            f"as {nat_public_ip}:{nat_public_port} | "
            f"dst_mac={host_public_mac} | "
            f"outport={public_openflow_port}",
        )

        self.connection.send(msg)
