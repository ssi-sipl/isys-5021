import socket
import struct
import math
import numpy as np
from sklearn.cluster import DBSCAN
from norfair import Detection, Tracker

# Define your own Euclidean distance function
def euclidean(detection: Detection, tracked_object):
    return np.linalg.norm(detection.points - tracked_object.estimate)

# Initialize the tracker
tracker = Tracker(
    distance_function=euclidean,
    distance_threshold=1  # Tune this based on your radar's scale
)

# Radar setup
UDP_IP = "192.168.252.2"
UDP_PORT = 2050
HEADER_SIZE = 256
DATA_PACKET_SIZE = 1012
HEADER_STRUCT = '<HHHHHHIHH'
DATA_STRUCT = '<' + 'H' + 'H' + '6f'*42

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
last_frame_id = None

while True:
    header_data, _ = sock.recvfrom(HEADER_SIZE)
    if len(header_data) != HEADER_SIZE:
        continue

    (
        frame_id, fw_major, fw_fix, fw_minor,
        nr_of_detections, nr_of_targets, crc,
        bytes_per_target, nr_of_data_packets
    ) = struct.unpack_from(HEADER_STRUCT, header_data, 0)

    # Frame loss detection
    if last_frame_id is not None:
        expected_id = (last_frame_id + 1) % 65536
        if frame_id != expected_id:
            print(f"⚠️ Frame loss: expected {expected_id}, got {frame_id}")
    last_frame_id = frame_id

    # Gather all targets
    targets = []
    for _ in range(nr_of_data_packets):
        packet, _ = sock.recvfrom(DATA_PACKET_SIZE)
        if len(packet) != DATA_PACKET_SIZE:
            continue
        vals = struct.unpack(DATA_STRUCT, packet)
        for i in range(42):
            base = 2 + i * 6
            sig, rng, vel, ang, _, _ = vals[base:base+6]
            
            if i < nr_of_targets:
                # if sig < 1 and rng < 3:
                targets.append({
                        'signal_dB': sig,
                        'range_m': rng,
                        'velocity_m_s': vel,
                        'angle_deg': ang
                })

    # Convert to x, y for clustering
    coords = []
    for t in targets:
        r = t['range_m']
        a = math.radians(t['angle_deg'])
        x = r * math.cos(a)
        y = r * math.sin(a)
        coords.append([x, y])

    coords = np.array(coords)
    detections = []

    # Cluster and prepare Norfair detections
    if len(coords) >= 2:
        db = DBSCAN(eps=1.0, min_samples=1).fit(coords)
        labels = db.labels_
        for i, t in enumerate(targets):
            t['cluster_id'] = labels[i]

        cluster_ids = set(t['cluster_id'] for t in targets if t['cluster_id'] != -1)
        for cid in cluster_ids:
            cluster_targets = [t for t in targets if t['cluster_id'] == cid]
            if len(cluster_targets) < 2:
                continue
            # avg_range = sum(t['range_m'] for t in cluster_targets) / len(cluster_targets)
            # avg_angle = sum(t['angle_deg'] for t in cluster_targets) / len(cluster_targets)
            # avg_velocity = sum(t['velocity_m_s'] for t in cluster_targets) / len(cluster_targets)
            # avg_signal   = sum(t['signal_dB']     for t in cluster_targets) / len(cluster_targets)
            
    #         print(f"Cluster {cid}: avg_range = {avg_range:.2f} m, "
    #   f"avg_angle = {avg_angle:.2f}°, "
    #   f"avg_velocity = {avg_velocity:.2f} m/s, "
    #   f"avg_signal = {avg_signal:.2f} dB")

            avg_x = np.mean([t['range_m'] * math.cos(math.radians(t['angle_deg'])) for t in cluster_targets])
            avg_y = np.mean([t['range_m'] * math.sin(math.radians(t['angle_deg'])) for t in cluster_targets])

            # Create Norfair detection
            detections.append(Detection(points=np.array([avg_x, avg_y])))
    else:
        # fallback if no clusters
        for t in targets:
            r = t['range_m']
            a = math.radians(t['angle_deg'])
            x = r * math.cos(a)
            y = r * math.sin(a)
            detections.append(Detection(points=np.array([x, y])))

    # Update tracker
    tracked_objects = tracker.update(detections=detections)

    print("\n✅ Tracked Objects:")
    for obj in tracked_objects:
        print(obj)
        # x, y = obj.estimate[0]
        # r = math.sqrt(x**2 + y**2)
        # angle = math.degrees(math.atan2(y, x))
        # print(f"Track ID {obj.id}: Range={r:.2f} m, Angle={angle:.2f}°")

    print("=" * 40)
