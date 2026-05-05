import struct
import time

# Flags
SYN = 0x0020

ACK = 0x0010

ERR = 0x0008

CTYP = 0x0004   # 1 = descarga,         0 = carga

PTYP = 0x0002   # 1 = selective repeat, 0 = stop & wait

FIN = 0x0001


def pcap_global_header():
    return struct.pack("<IHHiIII",
                       0xa1b2c3d4, 2, 4, 0, 0, 65535, 1
                       )


def pcap_packet_header(packet_len):
    return struct.pack("<IIII", int(time.time()), 0, packet_len, packet_len)


def ethernet_header():
    return b'\xff\xff\xff\xff\xff\xff' + b'\x00\x00\x00\x00\x00\x01' + b'\x08\x00'


def ip_header(payload_len):
    return struct.pack(">BBHHHBBH4s4s",
                       0x45, 0, 20 + 8 + payload_len, 1, 0, 64, 17, 0,
                       b'\x7f\x00\x00\x01', b'\x7f\x00\x00\x01'
                       )


def udp_header(payload_len):
    return struct.pack(">HHHH", 5000, 5000, 8 + payload_len, 0)


def rftp_packet(seq, flags, payload):
    word1 = (len(payload) << 5) & 0xFFE0
    word2 = flags & 0x003F
    return struct.pack(">HHHH", 0x1A2B, seq, word1, word2) + payload


def write_packet(f, seq, flags, payload, descripcion):
    pkt_rftp = rftp_packet(seq, flags, payload)
    pkt = ethernet_header() + ip_header(len(pkt_rftp)) + udp_header(len(pkt_rftp)) + pkt_rftp
    f.write(pcap_packet_header(len(pkt)))
    f.write(pkt)
    print(f"  Paquete {seq}: {descripcion}")


with open("test_rftp.pcap", "wb") as f:
    f.write(pcap_global_header())
    seq = 1

    print("=== Sesión 1: Carga con Stop & Wait ===")
    filesize = struct.pack(">I", 1024)  # 1024 bytes
    # CTYP=0 (carga), PTYP=0 (stop&wait)
    write_packet(f, seq, SYN, filesize + b"foto.jpg", "SYN carga stop&wait")
    seq += 1
    write_packet(f, seq, SYN | ACK, b"", "SYN+ACK")
    seq += 1
    write_packet(f, seq, ACK, b"chunk de datos 1", "Datos")
    seq += 1
    write_packet(f, seq, ACK, b"chunk de datos 2", "Datos")
    seq += 1
    write_packet(f, seq, FIN, b"", "FIN")
    seq += 1
    write_packet(f, seq, FIN | ACK, b"", "FIN+ACK")
    seq += 1

    print("=== Sesión 2: Carga con Selective Repeat ===")
    # CTYP=1 (descarga), PTYP=1 (selective repeat)
    write_packet(f, seq, SYN | CTYP | PTYP, b"video.mp4", "SYN descarga selective repeat")
    seq += 1
    write_packet(f, seq, SYN | ACK, b"", "SYN+ACK")
    seq += 1
    write_packet(f, seq, ACK, b"bloque 1", "Datos")
    seq += 1
    write_packet(f, seq, ACK, b"bloque 2", "Datos")
    seq += 1
    write_packet(f, seq, ACK | ERR, b"Retransmisin", "ACK+ERR (retransmisión)")
    seq += 1
    write_packet(f, seq, ACK, b"bloque 2 retransmitido", "Datos retransmitidos")
    seq += 1
    write_packet(f, seq, FIN, b"", "FIN")
    seq += 1
    write_packet(f, seq, FIN | ACK, b"", "FIN+ACK")
    seq += 1

print("\ntest_rftp.pcap generado.")
