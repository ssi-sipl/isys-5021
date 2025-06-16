import numpy as np
from radar_tracking2 import RadarTracker, process_and_track_targets
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
from config2 import *
import serial

ist_timezone = pytz.timezone('Asia/Kolkata')

targets_data = []  # List to store valid targets
tracked_targets_list = []
radar_tracker = RadarTracker(max_distance=3.0, max_age=5, hit_threshold=1)  # Reduced hit_threshold

# Debug counters
debug_stats = {
    'total_packets': 0,
    'valid_packets': 0,
    'total_detections': 0,
    'filtered_detections': 0,
    'signal_strength_filtered': 0,
    'velocity_filtered': 0,
    'range_filtered': 0
}

# Attempt to initialize the serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Serial Port Opened!")
except serial.SerialException as e:
    print(f"[ERROR] Failed to open serial port {SERIAL_PORT}: {e}")
    ser = None

def transmit_target_uart(target):
    if ser is None:
        print("[ERROR] Serial port is not available. Cannot send data.")
        return

    try:
        try:
            json_data = json.dumps(target)
        except (TypeError, ValueError) as e:
            print(f"[ERROR] JSON serialization failed: {e}")
            return
        
        try:
            encoded_data = (json_data + "\n").encode('utf-8')
        except UnicodeEncodeError as e:
            print(f"[ERROR] Encoding to UTF-8 failed: {e}")
            return
        
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
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_CHANNEL)
    elif rc == 5:
        print("❌ Connection refused: Not authorized. Check your username/password.")
        client.loop_stop()
        client.disconnect()
        raise SystemExit("Exiting due to authentication failure.")
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
    
    # Print debug statistics
    print("\n=== DEBUG STATISTICS ===")
    print(f"Total packets received: {debug_stats['total_packets']}")
    print(f"Valid packets processed: {debug_stats['valid_packets']}")
    print(f"Total raw detections: {debug_stats['total_detections']}")
    print(f"Detections after filtering: {debug_stats['filtered_detections']}")
    print(f"Filtered by signal strength: {debug_stats['signal_strength_filtered']}")
    print(f"Filtered by velocity: {debug_stats['velocity_filtered']}")
    print(f"Filtered by range: {debug_stats['range_filtered']}")
    
    tracked_targets = [track.get_state() for track in radar_tracker.tracks]
    with open("tracked_targets.json", "w") as file:
        json.dump(tracked_targets, file, indent=4)
    print("Tracked targets saved to tracked_targets.json")
    
    if SEND_MQTT:
        print("Disconnecting from MQTT broker...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def publish_target(target):
    try:
        mqtt_client.publish(MQTT_CHANNEL, json.dumps(target))
    except Exception as e:
        print(f"Failed to publish target: {e}")

# Improved angle smoothing filter
class AngleFilter:
    def __init__(self, window_size=3):
        self.window_size = window_size
        self.angle_history = []
    
    def filter_angle(self, new_angle):
        # Handle angle wrapping (-180 to 180 degrees)
        if len(self.angle_history) > 0:
            last_angle = self.angle_history[-1]
            # Check for angle wrapping
            if abs(new_angle - last_angle) > 180:
                if new_angle > last_angle:
                    new_angle -= 360
                else:
                    new_angle += 360
        
        self.angle_history.append(new_angle)
        if len(self.angle_history) > self.window_size:
            self.angle_history.pop(0)
        
        # Return smoothed angle
        smoothed = sum(self.angle_history) / len(self.angle_history)
        
        # Normalize to [-180, 180]
        while smoothed > 180:
            smoothed -= 360
        while smoothed < -180:
            smoothed += 360
            
        return smoothed

# Moving Average Filter with outlier detection
def moving_average_filter_with_outlier_detection(data, window_size=5, outlier_threshold=2.0):
    if len(data) < window_size:
        return data
    
    filtered_data = []
    for i in range(len(data)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(data), i + window_size // 2 + 1)
        window = data[start_idx:end_idx]
        
        # Calculate mean and std for outlier detection
        mean_val = np.mean(window)
        std_val = np.std(window)
        
        # Check if current value is an outlier
        if abs(data[i] - mean_val) > outlier_threshold * std_val and std_val > 0:
            # Replace outlier with mean
            filtered_data.append(mean_val)
        else:
            filtered_data.append(data[i])
    
    return filtered_data

# Enhanced Kalman Filter
class EnhancedKalmanFilter:
    def __init__(self, process_noise=1e-4, measurement_noise=0.05):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimate = 0
        self.error_estimate = 1
        self.is_initialized = False
        self.history = []
    
    def update(self, measurement):
        if not self.is_initialized:
            self.estimate = measurement
            self.is_initialized = True
            return self.estimate
        
        # Prediction
        prediction = self.estimate
        error_estimate = self.error_estimate + self.process_noise

        # Measurement update
        kalman_gain = error_estimate / (error_estimate + self.measurement_noise)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.error_estimate = (1 - kalman_gain) * error_estimate
        
        # Store history for debugging
        self.history.append({
            'measurement': measurement,
            'estimate': self.estimate,
            'kalman_gain': kalman_gain
        })
        
        # Keep only last 10 values
        if len(self.history) > 10:
            self.history.pop(0)

        return self.estimate

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

def parse_header(data):
    header_format = '<HHHHHHIHH118x'
    header_size = struct.calcsize(header_format)
    
    if len(data) < header_size:
        print("Incomplete header data.")
        return None
    
    frame_id, fw_major, fw_fix, fw_minor, detections, targets, checksum, bytes_per_target, data_packets = struct.unpack(
        header_format, data[:header_size]
    )

    print(f"Frame ID: {frame_id}, Detections: {detections}, Targets: {targets}")
    
    return detections, targets, data_packets, checksum, bytes_per_target, frame_id

# Global filters for consistency
velocity_filter = EnhancedKalmanFilter(process_noise=1e-5, measurement_noise=0.1)
range_filter = EnhancedKalmanFilter(process_noise=1e-6, measurement_noise=0.5)
angle_filter = AngleFilter(window_size=3)

def parse_data_packet(data, frame_id):
    global debug_stats
    
    target_format = '<ffffII'
    target_size = struct.calcsize(target_format)
    target_list = data[4:]
    
    targets = []
    raw_detections = 0
    
    for i in range(42):  # 42 targets per packet
        start = i * target_size
        end = start + target_size

        if end > len(target_list):
            break

        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)

        # Count all raw detections
        if signal_strength > 0 or range_ > 0 or velocity != 0 or azimuth != 0:
            raw_detections += 1
            debug_stats['total_detections'] += 1
            
            # Debug print for first few detections
            if raw_detections <= 5:
                print(f"Raw detection {raw_detections}: SS={signal_strength:.2f}dB, R={range_:.2f}m, V={velocity:.2f}m/s, A={azimuth:.2f}°")

        # Apply filters with debugging
        filter_reasons = []
        
        # Range filter - more lenient
        if range_ <= 0 or range_ > MAX_RANGE:
            filter_reasons.append(f"range({range_:.2f})")
            debug_stats['range_filtered'] += 1
            continue
            
        # Signal strength filter - more lenient for debugging
        if signal_strength < (SIGNAL_STRENGTH_THRESHOLD - 5):  # Temporarily reduced threshold
            filter_reasons.append(f"signal_strength({signal_strength:.2f})")
            debug_stats['signal_strength_filtered'] += 1
            continue
            
        # Velocity filter - allow more velocities for debugging
        if abs(velocity) < 0.1:  # Only filter very slow objects
            filter_reasons.append(f"velocity({velocity:.2f})")
            debug_stats['velocity_filtered'] += 1
            continue

        # Apply smoothing filters
        filtered_velocity = velocity_filter.update(velocity)
        filtered_range = range_filter.update(range_)
        filtered_azimuth = angle_filter.filter_angle(azimuth)
        
        # Clamp azimuth to valid range
        filtered_azimuth = max(-MAX_AZIMUTH, min(filtered_azimuth, MAX_AZIMUTH))

        # Calculate position
        azimuth_angle_radians = math.radians(filtered_azimuth)
        x = filtered_range * math.cos(azimuth_angle_radians)
        y = filtered_range * math.sin(azimuth_angle_radians)

        # Calculate GPS coordinates
        radar_lat_rad = math.radians(RADAR_LAT)
        delta_lat_deg = y / 111139
        delta_lon_deg = x / (111139 * math.cos(radar_lat_rad))
        object_lat = RADAR_LAT + delta_lat_deg
        object_lon = RADAR_LONG + delta_lon_deg

        # Classification
        try:
            classification = classification_pipeline(filtered_range, filtered_velocity, filtered_azimuth)
            if classification == "uav":
                classification = "others"
            elif classification == "bicycle":
                classification = "person"
        except:
            classification = "unknown"

        ist_timestamp = datetime.now(ist_timezone)

        target_info = {
            'radar_id': RADAR_ID,
            'area_id': AREA_ID,
            'frame_id': frame_id,
            'timestamp': str(ist_timestamp),
            'signal_strength': round(signal_strength, 2),
            'range': round(filtered_range, 2),
            'speed': round(abs(filtered_velocity), 2),  # Use absolute value
            'velocity_raw': round(velocity, 2),  # Keep raw velocity for debugging
            'aizmuth_angle': round(filtered_azimuth, 2),
            'azimuth_raw': round(azimuth, 2),  # Keep raw azimuth for debugging
            'distance': round(filtered_range, 2),
            'direction': "Static" if abs(velocity) < 0.1 else "Incoming" if velocity > 0 else "Outgoing",
            'classification': classification,
            'zone': 0,
            'x': round(x, 2),   
            'y': round(y, 2),
            'latitude': round(object_lat, 6),
            'longitude': round(object_lon, 6),
        }

        targets.append(target_info)
        targets_data.append(target_info)
        debug_stats['filtered_detections'] += 1
        
    print(f"Raw detections: {raw_detections}, Filtered detections: {len(targets)}")
        
    if targets:
        # Apply object tracking
        tracked_targets = process_and_track_targets(targets, radar_tracker)
        
        print(f"Frame ID: {frame_id}")
        print(f"Detected Targets: {len(targets)}, Tracked Targets: {len(tracked_targets)}")
        print(f"{'ID':<6} {'Track ID':<10} {'Range':<8} {'Speed':<8} {'Angle':<8} {'Raw Angle':<10} {'Class':<10} {'X':<8} {'Y':<8} {'Signal':<8}")
        print("-" * 90)
        
        for idx, target in enumerate(tracked_targets, start=1):
            if SEND_MQTT:
                publish_target(target)
            
            if SEND_UART:
                transmit_target_uart(target)

            track_id = target.get('track_id', 'New')
            raw_angle = target.get('azimuth_raw', 'N/A')

            print(f"{idx:<6} {track_id:<10} {target['range']:<8.1f} {target['speed']:<8.1f} "
                    f"{target['aizmuth_angle']:<8.1f} {raw_angle:<10} {target.get('tracked_classification', target['classification']):<10} "
                    f"{target['x']:<8.1f} {target['y']:<8.1f} {target['signal_strength']}")
            
        print("-" * 90)
    else:
        print(f"Frame ID: {frame_id} - No valid targets detected")

def process_packet(header_data, data_packet):
    global debug_stats
    debug_stats['total_packets'] += 1
    
    result = parse_header(header_data)
    if result is None:
        return
        
    detections, targets, data_packets, expected_checksum, bytes_per_target, frame_id = result
    
    packet_data = header_data + data_packet
    calculated_checksum = calculate_checksum(data_packet, targets, bytes_per_target)
    
    if calculated_checksum != expected_checksum:
        print(f"Checksum mismatch: Expected {expected_checksum}, Got {calculated_checksum}")
        return
    else:
        debug_stats['valid_packets'] += 1
        parse_data_packet(data_packet, frame_id=frame_id)

def main():
    header_size = 256
    data_packet_size = 1012
    
    print(f"Starting radar firmware with thresholds:")
    print(f"Signal Strength: {SIGNAL_STRENGTH_THRESHOLD}dB")
    print(f"Max Range: {MAX_RANGE}m")
    print(f"Max Azimuth: ±{MAX_AZIMUTH}°")
    print("-" * 50)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((LOCAL_IP, LOCAL_PORT))
        print(f"Listening on {LOCAL_IP}:{LOCAL_PORT}...")
        
        while True:
            try:
                header_data, addr = sock.recvfrom(header_size)
                data_packet, addr = sock.recvfrom(data_packet_size)
                if header_data and data_packet:
                    process_packet(header_data, data_packet)
            except Exception as e:
                print(f"Error processing packet: {e}")
                continue

if __name__ == "__main__":
    main()