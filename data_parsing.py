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

# Header: 6×uint16 + uint32 + 2×uint16 = 9 fields
HEADER_STRUCT = '<HHHHHHIHH'

# Data packet: uint16 frameID, uint16 packetNum, then 42×6 floats
DATA_STRUCT = '<' + 'H' + 'H' + '6f'*42

while True:
    # 1) receive header
    header_data, addr = sock.recvfrom(HEADER_SIZE)
    if len(header_data) != HEADER_SIZE:
        print("Warning: incomplete header received")
        continue

    # 2) unpack header
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

    print(f"\n=== HEADER ===")
    print(f"Frame ID             = {frame_id}")
    print(f"Firmware version     = {fw_major}.{fw_fix}.{fw_minor}")
    print(f"Detections reported  = {nr_of_detections}")
    print(f"Targets reported     = {nr_of_targets}")
    print(f"Bytes per target     = {bytes_per_target}")
    print(f"Data packets to follow = {nr_of_data_packets}")
    print(f"CRC                  = 0x{crc:08X}")

    # 3) read and decode each data packet
    for pkt_idx in range(1, nr_of_data_packets + 1):
        data_packet, addr = sock.recvfrom(DATA_PACKET_SIZE)
        if len(data_packet) != DATA_PACKET_SIZE:
            print(f"Warning: expected {DATA_PACKET_SIZE} bytes, got {len(data_packet)}")
            continue

        # unpack into a flat tuple: (frameID, packetNum, f1, f2, …)
        vals = struct.unpack(DATA_STRUCT, data_packet)
        dp_frame_id, packet_num = vals[0], vals[1]
        raw_floats = vals[2:]

        print(f"\n--- Data Packet {pkt_idx}/{nr_of_data_packets} ---")
        print(f"Packet frame ID = {dp_frame_id}, packet number = {packet_num}")

        # build list of up to 42 targets
        targets = []
        for i in range(42):
            base = i * 6
            sig, rng, vel, ang, _, _ = raw_floats[base:base+6]
            if i < nr_of_targets:  # only report the actual targets
                targets.append({
                    'signal_dB':        sig,
                    'range_m':          rng,
                    'velocity_m_s':     vel,
                    'angle_deg':        ang
                })
        # print them
        for idx, t in enumerate(targets, start=1):
            print(f"Target {idx:2d}:  signal={t['signal_dB']:.2f} dB, "
                  f"range={t['range_m']:.2f} m, "
                  f"vel={t['velocity_m_s']:.2f} m/s, "
                  f"angle={t['angle_deg']:.2f}°")
    print("=" * 40)
