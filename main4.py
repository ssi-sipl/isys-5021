import numpy as np
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
from config4 import *
import serial
from radar_tracker4 import update_tracks, Track

radar_tracker = []  # List of Track objects

ist_timezone = pytz.timezone('Asia/Kolkata')

final_data = []  # List to store valid targets


# Attempt to initialize the serial connection
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
            print(f"[INFO] Sent over UART: {json_data}")
        except serial.SerialTimeoutException as e:
            print(f"[ERROR] Serial write timeout: {e}")
        except serial.SerialException as e:
            print(f"[ERROR] Serial write failed: {e}")

    except Exception as e:
        print(f"[ERROR] Unexpected error in publish_target: {e}")

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
        json.dump(final_data, file, indent=4)
    print(f"Data saved to {OUTPUT_FILE}")

def signal_handler(sig, frame):
    print("\nCtrl+C detected! Saving data and exiting...")
    save_to_json()
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
    
    raw_detections = []
    
    for i in range(42):  # 42 targets per packet
        start = i * target_size
        end = start + target_size

        if end > len(target_list):
            # print(f"Warning: Not enough data to extract target {i}. Skipping.")
            break  # Stop processing if data is insufficient

        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)
        
        if not( MIN_SIGNAL_STRENGTH < signal_strength < MAX_SIGNAL_STRENGTH):
            continue
        
        if ( DETECT_ONLY_STATIC):
            if not( velocity == 0) :
                continue

        if ( DETECT_ONLY_MOVING):
            if not( velocity != 0) :
                continue

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

        classification = classification_pipeline(range_, velocity, azimuth)
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
            'velocity': round(velocity, 2), # speed
            'direction': "Static" if velocity == 0 else "Incoming" if velocity > 0 else "Outgoing",
            'classification': classification,
            'latitude': round(object_lat, 6),
            'longitude': round(object_lon, 6),
            'range': round(range_, 2),
            'azimuth': round(azimuth, 2), # aizmuth_angle
        }

        raw_detections.append(target_info)
    
    global radar_tracker
    radar_tracker = update_tracks(raw_detections, radar_tracker)

    if DEBUG_MODE:
        print(f"Frame ID: {frame_id}")
        print(f"Raw Targets: {len(raw_detections)}, Tracked Targets: {len(radar_tracker)}")     
        print(f"{'Track ID':<10} {'Range(m)':<8} {'Speed(m/s)':<8} {'Angle(deg)':<8} {'Class':<10} {'Signal Strength(dB)':<20} {'Confidence':<10} {'Missed Frames':<10}")
        
        print("-" * 80)
    for track in radar_tracker:

        tracked_data = track.get_state()
        if SEND_MQTT:
            publish_target(tracked_data)
        if SEND_UART:
            transmit_target_uart(tracked_data)

        if DEBUG_MODE:
            print(f"{tracked_data['track_id']:<10} {tracked_data['range']:<8} {tracked_data['velocity']:<8} {tracked_data['azimuth']:<8} {tracked_data['classification']:<20} {tracked_data['signal_strength']:<20} {tracked_data['confidence']:<10} {tracked_data['missed_frames']:<10}")
            print("-" * 80)

        final_data.append(tracked_data)

        
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
