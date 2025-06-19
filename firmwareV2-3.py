import socket
import struct
import math
import numpy as np
from sklearn.cluster import DBSCAN
from sort.sort import Sort  # <-- import SORT tracker
import statistics

# Setup radar connection
UDP_IP = "192.168.252.2"
UDP_PORT = 2050
HEADER_SIZE = 256
DATA_PACKET_SIZE = 1012

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

HEADER_STRUCT = '<HHHHHHIHH'
DATA_STRUCT = '<' + 'H' + 'H' + '6f'*42

last_frame_id = None
tracker = Sort()  # <-- initialize SORT tracker

while True:
    header_data, addr = sock.recvfrom(HEADER_SIZE)
    if len(header_data) != HEADER_SIZE:
        print("Warning: incomplete header received")
        continue

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

    targets = []

    for pkt_idx in range(1, nr_of_data_packets + 1):
        data_packet, addr = sock.recvfrom(DATA_PACKET_SIZE)
        if len(data_packet) != DATA_PACKET_SIZE:
            print(f"Warning: expected {DATA_PACKET_SIZE} bytes, got {len(data_packet)}")
            continue

        vals = struct.unpack(DATA_STRUCT, data_packet)
        dp_frame_id, packet_num = vals[0], vals[1]
        raw_floats = vals[2:]

        print(f"\n--- Data Packet {pkt_idx}/{nr_of_data_packets} ---")
        print(f"Packet frame ID = {dp_frame_id}, packet number = {packet_num}")

        for i in range(42):
            base = i * 6
            sig, rng, vel, ang, _, _ = raw_floats[base:base+6]
            if i < nr_of_targets:
                targets.append({
                    'signal_dB': sig,
                    'range_m': rng,
                    'velocity_m_s': vel,
                    'angle_deg': ang
                })

    coords = []
    for t in targets:
        r = t['range_m']
        a = math.radians(t['angle_deg'])
        x = r * math.cos(a)
        y = r * math.sin(a)
        coords.append([x, y])

    coords = np.array(coords)

    if len(coords) >= 2:
        db = DBSCAN(eps=1.0, min_samples=1).fit(coords)
        labels = db.labels_
        for i, t in enumerate(targets):
            t['cluster_id'] = labels[i]
    else:
        for t in targets:
            t['cluster_id'] = -1

    print("\n--- Real Object Clusters ---")
    cluster_ids = set(t['cluster_id'] for t in targets if t['cluster_id'] != -1)
    detections = []

    for cid in sorted(cluster_ids):
        cluster_targets = [t for t in targets if t['cluster_id'] == cid]
        if len(cluster_targets) < 2:
            continue

        avg_signal = sum(t['signal_dB'] for t in cluster_targets) / len(cluster_targets)
        if avg_signal < 1.0 or avg_signal > 15.0:
            continue

        try:
            std_range = statistics.stdev([t['range_m'] for t in cluster_targets])
        except statistics.StatisticsError:
            std_range = 0.0
        if std_range > 0.5:
            continue

        avg_range = sum(t['range_m'] for t in cluster_targets) / len(cluster_targets)
        avg_angle = sum(t['angle_deg'] for t in cluster_targets) / len(cluster_targets)
        r = avg_range
        a = math.radians(avg_angle)
        x = r * math.cos(a)
        y = r * math.sin(a)

        # SORT expects: [x1, y1, x2, y2, score]
        detections.append([x, y, x + 0.1, y + 0.1, avg_signal])  # dummy box size + confidence

    # Run SORT tracking
    if len(detections) > 0:
        tracks = tracker.update(np.array(detections))

        print("\n✅ SORT Tracked Objects:")
        for trk in tracks:
            x1, y1, x2, y2, track_id = trk
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            r = math.sqrt(cx**2 + cy**2)
            angle = math.degrees(math.atan2(cy, cx))
            print(f"Track ID {int(track_id)} → Range: {r:.2f} m, Angle: {angle:.2f}°")

    print("=" * 40)
