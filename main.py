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
mqtt_client = mqtt.Client()

try:
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
    print("Disconnecting from MQTT broker...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.exit(0)

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

def publish_target(target):
    try:
        mqtt_client.publish(MQTT_CHANNEL, json.dumps(target))
        print(f"Published target: {target}")
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
        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)

        # Filter targets below signal strength threshold
        if signal_strength < SIGNAL_STRENGTH_THRESHOLD:
            continue

        # Apply Kalman filter for velocity tracking
        filtered_velocity = kalman_filter_velocity.update(velocity)

        # calculating the x and y position of the target
        azimuth_angle_radians = math.radians(azimuth)
    
        # Calculate the x and y positions using trigonometry
        x = range_ * math.cos(azimuth_angle_radians)
        y = range_ * math.sin(azimuth_angle_radians)

        # Calculate the latitude and longitude of the object            
        
        radar_lat_rad = math.radians(RADAR_LAT) # Convert radar latitude to radians
        
        # Calculate change in latitude and longitude in degrees
        delta_lat_deg = y / 111139
        delta_lon_deg = x / (111139 * math.cos(radar_lat_rad))
        
        # Final coordinates of the object
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
            'classification': classification, # ['vehicle', 'person', 'bicycle', 'others']
            'zone': 0,
            'x': round(x, 2),   
            'y': round(y, 2),
            'latitude': round(object_lat, 6),
            'longitude': round(object_lon, 6),
        }

        targets.append(target_info)
        targets_data.append(target_info)

        publish_target(target_info)


        
    
    if targets:
        # process_and_print_targets(targets, frame_id)
        print(f"Frame ID: {frame_id}")
        print("Detected Targets:")
        print(f"{'Serial':<8} {'Signal Strength (dB)':<25} {'Range (m)':<15} {'Velocity (m/s)':<25} {'Direction':<15} {'Azimuth (Deg)':<25} {'x (m) y (m)':<25} {'Latitude':<25} {'Longitude':<25} {'Classification':<25}")
        print("-" * 150)
        for idx, target in enumerate(targets, start=1):        
            print(f"{idx:<8} {target['signal_strength']:<25} {target['range']:<15} {target['speed']:<25} {target['direction']:<15} {target['aizmuth_angle']:<25} {target['x']} {target['y']:<25} {target['latitude']:<25} {target['longitude']:<25} {target['classification']}")
                    
        print("-" * 50)

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
            if header_data:
                print("Header Data Received: ", len(header_data))
            if data_packet:
                print("Data Packet Received: ", len(data_packet))
            process_packet(header_data, data_packet)
            # print("-" * 50)
            

if __name__ == "__main__":
    main()
