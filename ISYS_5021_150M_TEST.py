import socket
import struct
import math
import numpy as np

# Define thresholds for valid detection
SNR_THRESHOLD = 3  # Example SNR threshold (in dB) Signal-to-Noise Ratio (SNR) 
SIGNAL_STRENGTH_THRESHOLD = 10  # Minimum valid signal strength (in dB)

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
    for i in range(nrOfTargets * bytesPerTarget):
        checksum += target_list[i]
        checksum &= 0xFFFFFFFF
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
        
        targets.append({
            'signal_strength': round(signal_strength, 2),
            'range': round(range_, 2),
            'velocity': round(filtered_velocity, 2),
            'azimuth': round(azimuth, 2),
            'x': round(x, 2),   
            'y': round(y, 2)
        })
    
   
    
    if targets:
        print(f"Frame ID: {frame_id}")
        print("Detected Targets:")
        print(f"{'Serial':<8} {'Signal Strength (dB)':<25} {'Range (m)':<15} {'Velocity (m/s)':<25} {'Direction':<15} {'Azimuth (Deg)':<25} {'x (m) y (m)':<25}")
        print("-" * 150)
        for idx, target in enumerate(targets, start=1):
            direction = "Static" if target["velocity"] == 0 else "Incomming" if target["velocity"] > 0 else "Outgoing"
            print(f"{idx:<8} {target['signal_strength']:<25} {target['range']:<15} {target['velocity']:<25} {direction:<15} {target['azimuth']:<25} {target['x']} {target['y']:<25}")
                    
        print("-" * 50)

    else:
        pass
        # print("No valid targets detected in this packet.")

# Process Packet
def process_packet(header_data, data_packet):
    detections, targets, data_packets, expected_checksum, bytes_per_target, frame_id = parse_header(header_data)
    
    if targets is None:
        return
    
    packet_data = header_data + data_packet
    calculated_checksum = calculate_checksum(data_packet, targets, bytes_per_target)
    
    if calculated_checksum != expected_checksum:
        # print(f"Checksum: Not Okay")
        pass
    else:
        # print(f"Checksum: Okay")
        parse_data_packet(data_packet, frame_id=frame_id)

# Main Loop
def main():
    local_ip = "192.168.252.2"
    local_port = 2050
    header_size = 256
    data_packet_size = 1012
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((local_ip, local_port))
        print(f"Listening on {local_ip}:{local_port}...")
        
        while True:
            header_data, addr = sock.recvfrom(header_size)
            data_packet, addr = sock.recvfrom(data_packet_size)
            # print("Packet Recieved")
            process_packet(header_data, data_packet)
            # print("-" * 50)

if __name__ == "__main__":
    main()
