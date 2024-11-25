import socket

# Configuration
local_ip = "192.168.252.2"  # Change to the IP address you want to bind
local_port = 2050  # Port 2050 as per your setup
buffer_size = 1024  # Adjust as needed

# Create a UDP socket
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the local address and port
udp_server_socket.bind((local_ip, local_port))

print(f"UDP server listening on {local_ip}:{local_port}")

try:
    while True:
        # Wait for incoming data
        data, addr = udp_server_socket.recvfrom(buffer_size)
        try:
            # Attempt to decode the data as UTF-8
            decoded_data = data.decode('utf-8')
            print(f"Received message from {addr}: {decoded_data}")
        except UnicodeDecodeError:
            # If decoding fails, print raw bytes
            print(f"Received non-UTF-8 data from {addr}: {data}")
        
        # Check if the data is coming from the expected sender
        if addr[0] == "192.168.252.10" and addr[1] == 2051:  # Expecting data from 192.168.252.10:2051
            print("Data is from the expected sender.")
        else:
            print("Data is from an unexpected sender.")
except KeyboardInterrupt:
    print("\nServer is shutting down.")
finally:
    udp_server_socket.close()
