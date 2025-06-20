import socket
import struct
import math
import numpy as np
from sklearn.cluster import DBSCAN
from norfair import Detection, Tracker
from datetime import datetime
import pytz
import serial
import json
import signal
import sys

from Classification.CLASSIFICATION_PIPELINE import classification_pipeline

ist_timezone = pytz.timezone('Asia/Kolkata')

final_data = []

# Define your own Euclidean distance function
def euclidean(detection: Detection, tracked_object):
    return np.linalg.norm(detection.points - tracked_object.estimate)

# Initialize the tracker
tracker = Tracker(
    distance_function=euclidean,
    distance_threshold=1  # Tune this based on your radar's scale
)

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 57600

def save_to_json():
    with open("FirmwareV2_Final_Data2.json", "w") as file:
        json.dump(final_data, file, indent=4)
    print(f"Data saved to FirmwareV2_Final_Data2.json")

def signal_handler(sig, frame):
    print("\nCtrl+C detected! Saving data and exiting...")
    save_to_json()
    # Disconnect MQTT
    sys.exit(0)

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Serial Port Opened!")
except serial.SerialException as e:
    print(f"[ERROR] Failed to open serial port {SERIAL_PORT}: {e}")
    ser = None  # Prevents using an invalid serial object

def transmit_target_uart(target):
    if ser is None:
        print("[ERROR] Serial port is not available. Cannot send data.")
        return

    try:
        # Attempt to serialize the data
        try:
            json_data = json.dumps(target)
        except (TypeError, ValueError) as e:
            print(f"[ERROR] JSON serialization failed: {e}")
            return
        
        # Attempt to encode the data
        try:
            encoded_data = (json_data + "\n").encode('utf-8')
        except UnicodeEncodeError as e:
            print(f"[ERROR] Encoding to UTF-8 failed: {e}")
            return
        
        # Attempt to write to the serial port
        try:
            ser.write(encoded_data)
            # print(f"[INFO] Sent over UART: {json_data}")
        except serial.SerialTimeoutException as e:
            print(f"[ERROR] Serial write timeout: {e}")
        except serial.SerialException as e:
            print(f"[ERROR] Serial write failed: {e}")

    except Exception as e:
        print(f"[ERROR] Unexpected error in publish_target: {e}")

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
                classification = classification_pipeline(rng, vel, ang)
                targets.append({
                            'signal_dB': sig,
                            'range_m': rng,
                            'velocity_m_s': vel,
                            'angle_deg': ang,
                            'classification': classification,
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
            detections.append(Detection(points=np.array([avg_x, avg_y]),data={"velocity_m_s": np.mean([t['velocity_m_s'] for t in cluster_targets]), "signal_dB": np.mean([t['signal_dB'] for t in cluster_targets])}))
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
        x, y = obj.estimate[0]
        r = math.sqrt(x**2 + y**2)
        angle = math.degrees(math.atan2(y, x))


        ist_timestamp = datetime.now(ist_timezone)
        # data = {
        #     "radar_id": "radar-pune",
        #     "area_id": "area-1",
        #     "frame_id": 20375,
        #     "timestamp": str(ist_timestamp)  ,
        #     "signal_strength": 0,
        #     "velocity": 0,
        #     "speed": 0,
        #     "direction": "Static",
        #     "classification": "person",
        #     "latitude": 34.011483,
        #     "longitude": 74.01246,
        #     "range": r,
        #     "distance": r,
        #     "aizmuth_angle": angle,
        #     "x": x,
        #     "y": y,
        #     "age": 0,
        #     "last_seen": "",
        #     "tracked_classification": "person",
        #     "track_id": obj.id,
        #     "zone": 0,
        # }


        data = {
            "radar_id": "radar-pune",
            "area_id": "area-1",
            "track_id": obj.id,
            "range":r,
            "angle": angle,
            "classification": "person",
            "timestamp": str(ist_timestamp)
        }
        final_data.append(data)

        transmit_target_uart(data)

        print(f"Track ID {obj.id}: Range={r:.2f} m, Angle={angle:.2f}°")


    print("=" * 40)
