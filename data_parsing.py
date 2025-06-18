import socket
import struct

# Set up the socket
UDP_IP = "192.168.252.2"  # Radar IP
UDP_PORT = 2050           # Radar port
HEADER_SIZE = 256
DATA_PACKET_SIZE = 1012

# Bind to local interface and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Define the binary‐layout of the first part of the header.
# Offsets (bytes) within the 256‑byte header:
#   0   frameID             uint16
#   2   FWmajor             uint16
#   4   FWfix               uint16
#   6   FWminor             uint16
#   8   nrOfDetections      uint16
#  10   nrOfTargets         uint16
#  12   crc                 uint32
#  16   bytesPerTarget      uint16
#  18   nrOfDataPackets     uint16
# (the remaining 256–20 = 236 bytes are reserved/padding)
HEADER_STRUCT = '<HHHHHHIHHH'  
#  ^ little-endian: H=uint16, I=uint32

while True:
    # 1) receive header
    header_data, addr = sock.recvfrom(HEADER_SIZE)
    if len(header_data) != HEADER_SIZE:
        print("Warning: incomplete header received")
        continue

    # 2) unpack header fields
    (
        frame_id,
        fw_major,
        fw_fix,
        fw_minor,
        nr_of_detections,
        nr_of_targets,
        crc,
        bytes_per_target,
        nr_of_data_packets
    ) = struct.unpack_from(HEADER_STRUCT, header_data, 0)

    print(f"Header:")
    print(f"  Frame ID           = {frame_id}")
    print(f"  Firmware version   = {fw_major}.{fw_fix}.{fw_minor}")
    print(f"  Detections reported= {nr_of_detections}")
    print(f"  Targets reported   = {nr_of_targets}")
    print(f"  Bytes per target   = {bytes_per_target}")
    print(f"  Data packets to follow = {nr_of_data_packets}")
    print(f"  CRC                = 0x{crc:08X}")

    # 3) now you know how many data packets to read:
    for i in range(nr_of_data_packets):
        data_packet, addr = sock.recvfrom(DATA_PACKET_SIZE)
        if len(data_packet) != DATA_PACKET_SIZE:
            print(f"Warning: expected {DATA_PACKET_SIZE} bytes, got {len(data_packet)}")
        else:
            print(f"Received data packet #{i+1} ({len(data_packet)} bytes)")

    print("-" * 40)
