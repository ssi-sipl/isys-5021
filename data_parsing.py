import socket
import struct
import math
import numpy as np
from sklearn.cluster import DBSCAN

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

last_frame_id = None  # for frame loss detection

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

    # Detect frame loss
    if last_frame_id is not None:
        expected_id = (last_frame_id + 1) % 65536
        if frame_id != expected_id:
            print(f"[WARNING] Frame loss detected! Expected {expected_id}, got {frame_id}")
    last_frame_id = frame_id

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
                if sig < 1 and rng < 3:  # Optional filters
                    targets.append({
                            'signal_dB': sig,
                            'range_m': rng,
                            'velocity_m_s': vel,
                            'angle_deg': ang
                    })

        # Convert (range, angle) → (x, y) for clustering
        coords = []
        for t in targets:
            r = t['range_m']
            a = math.radians(t['angle_deg'])
            x = r * math.cos(a)
            y = r * math.sin(a)
            coords.append([x, y])

        coords = np.array(coords)

        # Perform clustering if enough points
        if len(coords) >= 1:
            db = DBSCAN(eps=1.0, min_samples=1).fit(coords)
            labels = db.labels_
            for i, t in enumerate(targets):
                t['cluster_id'] = labels[i]
        else:
            for t in targets:
                t['cluster_id'] = -1

        # Print clustered targets
        print("\n--- Clustered Targets ---")
        cluster_ids = set(t['cluster_id'] for t in targets)
        for cid in sorted(cluster_ids):
            cluster_targets = [t for t in targets if t['cluster_id'] == cid]
            avg_range = sum(t['range_m'] for t in cluster_targets) / len(cluster_targets)
            avg_angle = sum(t['angle_deg'] for t in cluster_targets) / len(cluster_targets)
            avg_velocity = sum(t['velocity_m_s'] for t in cluster_targets) / len(cluster_targets)
            avg_signal   = sum(t['signal_dB']     for t in cluster_targets) / len(cluster_targets)
            print(f"Cluster {cid}: avg_range = {avg_range:.2f} m, "
      f"avg_angle = {avg_angle:.2f}°, "
      f"avg_velocity = {avg_velocity:.2f} m/s, "
      f"avg_signal = {avg_signal:.2f} dB")
            # print(f"\nCluster {cid}:")
            # for t in [t for t in targets if t['cluster_id'] == cid]:
            #     print(f"  signal={t['signal_dB']:.2f} dB, "
            #           f"range={t['range_m']:.2f} m, "
            #           f"vel={t['velocity_m_s']:.2f} m/s, "
            #           f"angle={t['angle_deg']:.2f}°")
    print("=" * 40)
