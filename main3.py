# Checksum Calculation
import socket
import struct
import math
from config import LOCAL_IP, LOCAL_PORT


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

    # print(f"Frame ID: {frame_id}")
    # print(f"Number of Targets: {targets}")
    
    return detections, targets, data_packets, checksum, bytes_per_target, frame_id

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

def parse_data_packet(data, frame_id):
    target_format = '<ffffII'  # Signal Strength, Range, Velocity, Azimuth, Reserved1, Reserved2
    target_size = struct.calcsize(target_format)
    target_list = data[4:]
    
    targets = []
    
    for i in range(42):  # 42 targets per packet
        start = i * target_size
        end = start + target_size

        if end > len(target_list):
            # print(f"Warning: Not enough data to extract target {i}. Skipping.")
            break  # Stop processing if data is insufficient

        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)

        print(f"Target {i+1}: Signal Strength: {signal_strength}, Range: {range_}, Velocity: {velocity}, Azimuth: {azimuth}")
        print("-" * 50)
    

        

        # if velocity == 0 :
        #     # cluter filtering
        #     continue
        # # Filter targets below signal strength threshold
        # if signal_strength < SIGNAL_STRENGTH_THRESHOLD:
        #     continue

 






        # Calculate the x and y position of the target
        azimuth_angle_radians = math.radians(azimuth)
        x = range_ * math.cos(azimuth_angle_radians)
        y = range_ * math.sin(azimuth_angle_radians)

        # Calculate the latitude and longitude of the object            
        # radar_lat_rad = math.radians(RADAR_LAT)
        # delta_lat_deg = y / 111139
        # delta_lon_deg = x / (111139 * math.cos(radar_lat_rad))
        # object_lat = RADAR_LAT + delta_lat_deg
        # object_lon = RADAR_LONG + delta_lon_deg

        # classification = classification_pipeline(range_, filtered_velocity, azimuth)
        # if classification=="uav":
        #     classification="others"
        # elif classification=="bicycle":
        #     classification="person"

        # ist_timestamp = datetime.now(ist_timezone)

        target_info = {
            # 'radar_id': "radar-pune",
            # 'area_id': "area-1",
            'frame_id': frame_id,
            # 'timestamp': str(ist_timestamp),
            'signal_strength': round(signal_strength, 2),
            'range': round(range_, 2),
            'velocity': round(velocity, 2),
            'aizmuth_angle': round(azimuth, 2),
            # 'distance': round(range_, 2),
            'direction': "Static" if velocity == 0 else "Incoming" if velocity > 0 else "Outgoing",
            # 'classification': classification,
            # 'zone': 0,
            # 'x': round(x, 2),   
            # 'y': round(y, 2),
            # 'latitude': round(object_lat, 6),
            # 'longitude': round(object_lon, 6),
        }

        targets.append(target_info)
        # targets_data.append(target_info)
        
    if targets:
        # Apply object tracking to the detected targets
        
        # print("-" * 80)
        # print(f"Frame ID: {frame_id}")
        # print(f"Detected Targets: {len(targets)}")
        # print(f"{'Signal Strength':<20} {'Range (m)':<10} {'velocity (m/s)':<10} {'Azimuth (deg)':<15} {'Direction':<10}")

        # print("-" * 80)

        # for target in targets:
        #     print(f"{target['signal_strength']:<20} {target['range']:<10.1f} {target['velocity']:<10.1f} "
        #           f"{target['aizmuth_angle']:<15.1f} {target['direction']:<10}")
        # print("-" * 80)




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

