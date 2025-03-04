import numpy as np
from radar_tracking import RadarTracker, process_and_track_targets
import socket
import struct
import math
import numpy as np
import json
import signal
import sys
import pytz
from datetime import datetime
import paho.mqtt.client as mqtt
from Classification.CLASSIFICATION_PIPELINE import classification_pipeline
from config import *


ist_timezone = pytz.timezone('Asia/Kolkata')

targets_data = []  # List to store valid targets

radar_tracker = RadarTracker(max_distance=5.0, max_age=3, hit_threshold=2)

def on_connect(client, userdata, flags, rc):
        # global is_connected_to_mqtt_flag
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_CHANNEL)
            # is_connected_to_mqtt_flag = True
        elif rc == 5:
            print("❌ Connection refused: Not authorized. Check your username/password.")
            client.loop_stop()  # Stop the MQTT loop
            client.disconnect()  # Disconnect cleanly
            raise SystemExit("Exiting due to authentication failure.")  # Stop script execution
        else:
            print(f"⚠️ Connection failed with result code {rc}")
            client.loop_stop()
            client.disconnect()
            raise SystemExit("Exiting due to connection failure.")


if SEND_MQTT:
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
     
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("Channel: ", MQTT_CHANNEL)
        print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        sys.exit(1)


def save_to_json():
    with open(OUTPUT_FILE, "w") as file:
        json.dump(targets_data, file, indent=4)
    print(f"Data saved to {OUTPUT_FILE}")

def signal_handler(sig, frame):
    print("\nCtrl+C detected! Saving data and exiting...")
    save_to_json()
    
    # Save tracked targets
    tracked_targets = [track.get_state() for track in radar_tracker.tracks]
    with open("tracked_targets.json", "w") as file:
        json.dump(tracked_targets, file, indent=4)
    print("Tracked targets saved to tracked_targets.json")
    
    # Disconnect MQTT
    if SEND_MQTT:
        print("Disconnecting from MQTT broker...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    sys.exit(0)

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

def publish_target(target):
    try:
        mqtt_client.publish(MQTT_CHANNEL, json.dumps(target))
        # print(f"Published target: {target}")
    except Exception as e:
        print(f"Failed to publish target: {e}")

# Simple Moving Average Filter
def moving_average_filter(data, window_size=5):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# Kalman Filter setup (simple version)
class KalmanFilter:
    def __init__(self, process_noise=1e-5, measurement_noise=0.1, estimated_measurement_error=1e-1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimated_measurement_error = estimated_measurement_error
        self.estimate = 0
        self.error_estimate = 1
    
    def update(self, measurement):
        # Prediction
        prediction = self.estimate
        error_estimate = self.error_estimate + self.process_noise

        # Measurement update
        kalman_gain = error_estimate / (error_estimate + self.measurement_noise)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.error_estimate = (1 - kalman_gain) * error_estimate

        return self.estimate

# Checksum Calculation
def calculate_checksum(data, nrOfTargets, bytesPerTarget):
    target_list = data[4:]
    checksum = 0

    try:
        for i in range(nrOfTargets * bytesPerTarget):
            checksum += target_list[i]
            checksum &= 0xFFFFFFFF
        
    except IndexError:
         print("Warning: Index out of range while calculating checksum. Ignoring and continuing...")

    return checksum

# Parse Header
def parse_header(data):
    header_format = '<HHHHHHIHH118x'
    header_size = struct.calcsize(header_format)
    
    if len(data) < header_size:
        print("Incomplete header data.")
        return None
    
    frame_id, fw_major, fw_fix, fw_minor, detections, targets, checksum, bytes_per_target, data_packets = struct.unpack(
        header_format, data[:header_size]
    )

    # print(f"Frame ID: {frame_id}")
    # print(f"Number of Targets: {targets}")
    
    return detections, targets, data_packets, checksum, bytes_per_target, frame_id

# Parse Data Packet
def parse_data_packet(data, frame_id):
    target_format = '<ffffII'  # Signal Strength, Range, Velocity, Azimuth, Reserved1, Reserved2
    target_size = struct.calcsize(target_format)
    target_list = data[4:]
    
    targets = []
    kalman_filter_velocity = KalmanFilter()
    
    for i in range(42):  # 42 targets per packet
        start = i * target_size
        end = start + target_size

        if end > len(target_list):
            # print(f"Warning: Not enough data to extract target {i}. Skipping.")
            break  # Stop processing if data is insufficient

        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)

        if velocity == 0 :
            # cluter filtering
            continue
        # Filter targets below signal strength threshold
        if signal_strength < SIGNAL_STRENGTH_THRESHOLD:
            continue

        # Apply Kalman filter for velocity tracking
        filtered_velocity = kalman_filter_velocity.update(velocity)


        # Calculate the x and y position of the target
        azimuth_angle_radians = math.radians(azimuth)
        x = range_ * math.cos(azimuth_angle_radians)
        y = range_ * math.sin(azimuth_angle_radians)

        # Calculate the latitude and longitude of the object            
        radar_lat_rad = math.radians(RADAR_LAT)
        delta_lat_deg = y / 111139
        delta_lon_deg = x / (111139 * math.cos(radar_lat_rad))
        object_lat = RADAR_LAT + delta_lat_deg
        object_lon = RADAR_LONG + delta_lon_deg

        classification = classification_pipeline(range_, filtered_velocity, azimuth)
        if classification=="uav":
            classification="others"
        elif classification=="bicycle":
            classification="person"

        ist_timestamp = datetime.now(ist_timezone)

        target_info = {
            'radar_id': "radar-pune",
            'area_id': "area-1",
            'frame_id': frame_id,
            'timestamp': str(ist_timestamp),
            'signal_strength': round(signal_strength, 2),
            'range': round(range_, 2),
            'speed': round(filtered_velocity, 2),
            'aizmuth_angle': round(azimuth, 2),
            'distance': round(range_, 2),
            'direction': "Static" if velocity == 0 else "Incoming" if velocity > 0 else "Outgoing",
            'classification': classification,
            'zone': 0,
            'x': round(x, 2),   
            'y': round(y, 2),
            'latitude': round(object_lat, 6),
            'longitude': round(object_lon, 6),
        }

        targets.append(target_info)
        targets_data.append(target_info)
        
    if targets:
        # Apply object tracking to the detected targets
        tracked_targets = process_and_track_targets(targets, radar_tracker)
        
        # for target in tracked_targets:
        #     print (target)

        # Publish tracked targets via MQTT if enabled
        if SEND_MQTT:
            for target in tracked_targets:
                publish_target(target)
        
        # Display the tracked targets
        print(f"Frame ID: {frame_id}")
        print(f"Detected Targets: {len(targets)}, Tracked Targets: {len(tracked_targets)}")
        print(f"{'ID':<6} {'Track ID':<10} {'Range':<8} {'Speed':<8} {'Angle':<8} {'Class':<10} {'X':<8} {'Y':<8} {'Signal Strenght':<20}")
        print("-" * 80)
        
        for idx, target in enumerate(tracked_targets, start=1):
            track_id = target.get('track_id', 'New')
            print(f"{idx:<6} {track_id:<10} {target['range']:<8.1f} {target['speed']:<8.1f} "
                  f"{target['aizmuth_angle']:<8.1f} {target['tracked_classification']:<10} "
                  f"{target['x']:<8.1f} {target['y']:<8.1f} {target["signal_strength"]}")
        
        print("-" * 80)


# Process Packet
def process_packet(header_data, data_packet):
    detections, targets, data_packets, expected_checksum, bytes_per_target, frame_id = parse_header(header_data)
    
    if targets is None:
        return
    
    packet_data = header_data + data_packet
    calculated_checksum = calculate_checksum(data_packet, targets, bytes_per_target)
    
    if calculated_checksum != expected_checksum:
        # print(f"Checksum: Not Okay")
        return
    else:
        # print(f"Checksum: Okay")
        parse_data_packet(data_packet, frame_id=frame_id)

# Main Loop
def main():
    header_size = 256
    data_packet_size = 1012
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((LOCAL_IP, LOCAL_PORT))
        print(f"Listening on {LOCAL_IP}:{LOCAL_PORT}...")
        
        while True:
            header_data, addr = sock.recvfrom(header_size)
            data_packet, addr = sock.recvfrom(data_packet_size)
            if header_data and data_packet:
                # print("Packet Received")
                
                process_packet(header_data, data_packet)
            # print("-" * 50)
            

if __name__ == "__main__":
    main()
