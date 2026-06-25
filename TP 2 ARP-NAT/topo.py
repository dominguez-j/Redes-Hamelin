#!/usr/bin/python3

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo

#                                      Tráfico Saliente
#
#                                      <---------------
#
#                           Red Pública                Red Privada
#
#
#                              port 1                     port 2
#        ┌───────┐     IP:  200.0.0.254        /\  IP: 192.168.1.254          ┌───────┐
#        │       │     MAC: 00.00.00.aa.aa.aa /  \ MAC:00.00.00.bb.bb.bb      │       │
#        │  h1   ├───────────────────────────/ s1 \───────────────────────────│  h2   │
#        └───────┘                           \    /                           └───────┘
#       /       /                             \  /                           /       /
#      ─────────                               \/                           ─────────
#  IP:  200.0.0.1/24                                                    IP:  192.168.1.2/24
#  DG:  200.0.0.254                                                     DG:  192.168.1.254
#  MAC: 00:00:00:00:00:01                                               MAC: 00:00:00:00:00:02
#


class NATTopo(Topo):
    def build(self):
        s1 = self.addSwitch("s1")

        h1 = self.addHost(
            "h1",
            ip="200.0.0.1/24",
            mac="00:00:00:00:00:01",
            defaultRoute="via 200.0.0.254",
        )

        h2 = self.addHost(
            "h2",
            ip="192.168.1.2/24",
            mac="00:00:00:00:00:02",
            defaultRoute="via 192.168.1.254",
        )

        h3 = self.addHost(
            "h3",
            ip="192.168.1.3/24",
            mac="00:00:00:00:00:03",
            defaultRoute="via 192.168.1.254",
        )

        h4 = self.addHost(
            "h4",
            ip="192.168.1.4/24",
            mac="00:00:00:00:00:04",
            defaultRoute="via 192.168.1.254",
        )

        self.addLink(h1, s1, port2=1)
        self.addLink(h2, s1, port2=2)
        self.addLink(h3, s1, port2=3)
        self.addLink(h4, s1, port2=4)


def run():
    topo = NATTopo()
    net = Mininet(topo=topo, controller=RemoteController, link=TCLink)
    net.start()

    # Deshabilita IPv6 en hosts
    for host in net.hosts:
        host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        host.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        host.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    # Deshabilita IPv6 en switch
    s1 = net.get("s1")
    s1.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    s1.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    s1.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    # Entradas ARP para debug (TODO: Usar Protocolo ARP)
    # net.get("h1").setARP("200.0.0.254", "00:00:00:aa:aa:aa")
    # net.get("h2").setARP("192.168.1.254", "00:00:00:bb:bb:bb")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
