import socket
import struct
import math

def calculate_checksum(data, nrOfTargets, bytesPerTarget):
    # List of targets (42 targets per packet)
    target_list = data[4:]
    checksum = 0
    for i in range(nrOfTargets * bytesPerTarget):
        checksum += target_list[i]
        checksum &= 0xFFFFFFFF  # Ensure it fits within a 32-bit boundary
    return checksum
    
def parse_header(data):
    """
    Parse the 256-byte header and print relevant information.
    """
    header_format = '<HHHHHHIHH118x'  # Define the header structure
    header_size = struct.calcsize(header_format)
    
    if len(data) < header_size:
        print("Incomplete header data.")
        return None  # Return None if header is incomplete
    
    # Unpack the header data
    frame_id, fw_major, fw_fix, fw_minor, detections, targets, checksum, bytes_per_target, data_packets = struct.unpack(
        header_format, data[:header_size]
    )
    
    print(f"Frame ID: {frame_id}")
    # print(f"Firmware Version: {fw_major}.{fw_minor}.{fw_fix}")
    # print(f"Number of Detections: {detections}")
    print(f"Number of Serials: {targets}")
    # print(f"Bytes per Target: {bytes_per_target}")
    # print(f"Number of Data Packets: {data_packets}")
    # print(f"Checksum: {hex(checksum)}")
    
    return detections, targets, data_packets, checksum, bytes_per_target

def parse_data_packet(data):
    target_format = '<ffffII'  # Signal Strength, Range, Velocity, Azimuth, Reserved1, Reserved2
    target_size = struct.calcsize(target_format)

    frame_id, number_of_data_packet = struct.unpack('<HH', data[:4])
    target_list = data[4:]
    
    targets = []
    for i in range(42):  # 42 targets per packet
        target_data = target_list[i * target_size:(i + 1) * target_size]
        signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)
        
        if signal_strength == 0 and range_ == 0 and velocity == 0 and azimuth == 0:
            continue
        
        targets.append({
            'signal_strength': round(signal_strength, 2),
            'range': round(range_, 2),
            'velocity': round(velocity, 2),
            'azimuth': round(azimuth, 2),
        })
    
    if targets:
        print("Serial List:")
        print(f"{'Serial':<8} {'Signal Strength (dB)':<25} {'Range (m)':<15} {'Velocity (m/s)':<25} {'Direction':<15} {'Azimuth (Deg)'}")
        print("-" * 110)
        for idx, target in enumerate(targets, start=1):
            direction = "Static" if target["velocity"]==0 else "Incomming" if target["velocity"]>0 else "Outgoing"
            
            
            print(f"{idx:<8} {target['signal_strength']:<25} {target['range']:<15} {target['velocity']:<25} {direction:<15}  {target['azimuth']}")
    else:
        print(f"Frame ID: {frame_id}, Data Packet Number: {number_of_data_packet} contains no valid targets.")

def process_packet(header_data, data_packet):
    """
    Process a single pair of packets that includes both the header (256 bytes) and data packet (1024 bytes).
    """
    detections, targets, data_packets, expected_checksum, bytes_per_target = parse_header(header_data)
    
    if targets is None:
        return  # If header parsing failed, return
    
    packet_data = header_data + data_packet  # Concatenate header and data
    calculated_checksum = calculate_checksum(data_packet, targets, bytes_per_target)
    
    if calculated_checksum != expected_checksum:
        print(f"Checksum: Not Okay")
    else:
        print(f"Checksum: Okay")
        parse_data_packet(data_packet)

def main():
    # local_ip = "127.0.0.1"  # Bind to all available interfaces
    local_ip = "192.168.252.2"  # Bind to all available interfaces
    local_port = 2050  # Listening on the same port as the radar

    header_size = 256  # Header packet size
    data_packet_size = 1012  # Data packet size

    max_packet_size = max(header_size, data_packet_size)  # Max size for a single packet

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((local_ip, local_port))
        print(f"Listening on {local_ip}:{local_port}...")
        frame_count = 0

        while True:
            frame_count += 1

            header_data, addr = sock.recvfrom(header_size)
            data_packet, addr = sock.recvfrom(data_packet_size)
            print("Packet Recieved")

            process_packet(header_data, data_packet)

            print(f"Total frames received: {frame_count}")
            print("-" * 50)

if __name__ == "__main__":
    main()
