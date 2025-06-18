import socket

# Set up the socket
UDP_IP = "192.168.252.2"  # Radar IP
UDP_PORT = 2050           # Radar port
BUFFER_SIZE = 4096        # Adjust based on expected packet size
header_size = 256
data_packet_size = 1012

# Bind to local interface and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for data from radar at {UDP_IP}:{UDP_PORT}")

while True:
    
    header_data, addr = sock.recvfrom(header_size)
    print(f"Received header data from {len(header_data)} bytes from {addr}")
    # print(header_data.hex())  # For debugging raw header data
    data_packet, addr = sock.recvfrom(data_packet_size)
    print(f"Received data packet from {len(data_packet)} bytes from {addr}")
    # print(data_packet.hex())  # For debugging raw data packet

    print("-" * 40)
