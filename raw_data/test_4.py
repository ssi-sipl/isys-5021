import socket
import tkinter as tk
from tkinter import scrolledtext
import threading
import struct

# Configuration
local_ip = "192.168.252.2"  # IP to listen on
local_port = 2050            # Port to listen on
buffer_size = 2048           # Adjust as needed

# UDP server class
class UDPServer:
    def __init__(self, ip, port, gui):
        self.ip = ip
        self.port = port
        self.gui = gui
        self.running = False
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        """Start the UDP server."""
        self.udp_socket.bind((self.ip, self.port))
        self.running = True
        self.gui.update_status("Server running...")
        self.receive_data()

    def stop(self):
        """Stop the UDP server."""
        self.running = False
        self.udp_socket.close()
        self.gui.update_status("Server stopped.")

    def receive_data(self):
        """Receive data from the UDP socket."""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(buffer_size)
                # Handle data only if it comes from the expected source
                if addr[1] == 2051:  # Assuming specific port validation
                    self.process_packet(data, addr)
            except Exception as e:
                if self.running:
                    self.gui.display_received_data(f"Error: {e}")
                break

    def process_packet(self, packet, addr):
        """Process the received raw packet and display decoded information."""
        try:
            # Check minimum packet size (Ethernet+IPv4+UDP+target data header size)
            if len(packet) < 46:  # Ethernet (14) + IPv4 (20) + UDP (8) + FrameID+Packet# (4)
                self.gui.display_received_data(f"Packet too short: {len(packet)} bytes")
                return

            # Unpack headers
            dest_mac, src_mac, ether_type = self.unpack_ethernet_header(packet)
            version, ihl, total_length, protocol, src_ip, dest_ip = self.unpack_ipv4_header(packet)
            src_port, dest_port, udp_length, udp_checksum = self.unpack_udp_header(packet)

            # Unpack target data packet
            frame_id, packet_number, targets, checksum_received = self.unpack_target_data_packet(packet[42:])

            # Prepare output for the GUI
            output = f"Received from {addr}:\n"
            output += "Ethernet II Header:\n"
            output += f"  Destination MAC: {dest_mac}\n"
            output += f"  Source MAC: {src_mac}\n"
            output += f"  EtherType: {hex(ether_type)}\n"
            
            output += "\nIPv4 Header:\n"
            output += f"  Version: {version}\n"
            output += f"  IHL: {ihl}\n"
            output += f"  Total Length: {total_length}\n"
            output += f"  Protocol: {protocol}\n"
            output += f"  Source IP: {src_ip}\n"
            output += f"  Destination IP: {dest_ip}\n"
            
            output += "\nUDP Header:\n"
            output += f"  Source Port: {src_port}\n"
            output += f"  Destination Port: {dest_port}\n"
            output += f"  Length: {udp_length}\n"
            output += f"  Checksum: {udp_checksum}\n"
            
            output += "\nTarget Data Packet:\n"
            output += f"  Frame ID: {frame_id}\n"
            output += f"  Packet Number: {packet_number}\n"
            output += "  Targets:\n"
            for i, target in enumerate(targets):
                output += f"    Target {i + 1}:\n"
                output += f"      Signal Strength: {target['signal_strength']} dB\n"
                output += f"      Range: {target['range']} m\n"
                output += f"      Velocity: {target['velocity']} m/s\n"
                output += f"      Azimuth Angle: {target['azimuth_angle']}°\n"
                output += f"      Reserved1: {target['reserved1']}\n"
                output += f"      Reserved2: {target['reserved2']}\n"

            output += f"\nChecksum Received: {checksum_received}\n"
            self.gui.display_received_data(output)

        except Exception as e:
            self.gui.display_received_data(f"Failed to process packet: {e}")

    # Unpacking methods
    def unpack_ethernet_header(self, packet):
        """Unpack the Ethernet II header."""
        eth_header = struct.unpack('!6s6sH', packet[:14])  # 6+6+2 bytes
        dest_mac = ':'.join(format(b, '02x') for b in eth_header[0])
        src_mac = ':'.join(format(b, '02x') for b in eth_header[1])
        ether_type = eth_header[2]
        return dest_mac, src_mac, ether_type

    def unpack_ipv4_header(self, packet):
        """Unpack the IPv4 header."""
        ipv4_header = struct.unpack('!BBHHHBBH4s4s', packet[14:34])  # 20 bytes
        version_ihl = ipv4_header[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0x0F
        total_length = ipv4_header[2]
        protocol = ipv4_header[6]
        src_ip = socket.inet_ntoa(ipv4_header[8])
        dest_ip = socket.inet_ntoa(ipv4_header[9])
        return version, ihl, total_length, protocol, src_ip, dest_ip

    def unpack_udp_header(self, packet):
        """Unpack the UDP header."""
        udp_header = struct.unpack('!HHHH', packet[34:42])  # 8 bytes
        src_port = udp_header[0]
        dest_port = udp_header[1]
        udp_length = udp_header[2]
        udp_checksum = udp_header[3]
        return src_port, dest_port, udp_length, udp_checksum

    def unpack_target_data_packet(self, data):
        """Unpack the target data packet."""
        if len(data) < 4:
            raise ValueError("Target data packet too short.")

        # Unpack frame ID and packet number
        frame_id, packet_number = struct.unpack('<HH', data[:4])

        # Unpack targets
        targets = []
        for i in range(42):  # Maximum of 42 targets per packet
            target_start = 4 + i * 24  # Each target is 24 bytes
            if target_start + 24 > len(data):
                break
            target_data = struct.unpack('<ffffff', data[target_start:target_start + 24])
            target = {
                'signal_strength': target_data[0],
                'range': target_data[1],
                'velocity': target_data[2],
                'azimuth_angle': target_data[3],
                'reserved1': target_data[4],
                'reserved2': target_data[5]
            }
            targets.append(target)

        # Unpack checksum
        checksum_start = 4 + len(targets) * 24
        if checksum_start + 4 > len(data):
            raise ValueError("Checksum missing in target data packet.")
        checksum_received = struct.unpack('<I', data[checksum_start:checksum_start + 4])[0]

        return frame_id, packet_number, targets, checksum_received

# GUI class using tkinter
class UDPServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP Server")

        # Create text box to display received data
        self.text_box = scrolledtext.ScrolledText(root, width=50, height=15)
        self.text_box.pack(padx=10, pady=10)

        # Create status label
        self.status_label = tk.Label(root, text="Status: Stopped", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)

        # Create buttons
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_button.pack(side="left", padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_button.pack(side="right", padx=10, pady=10)

        self.clear_button = tk.Button(root, text="Clear", command=self.clear_data)
        self.clear_button.pack(side="bottom", padx=10, pady=10)

        # Create UDP server instance
        self.udp_server = UDPServer(local_ip, local_port, self)

    def start_server(self):
        """Start the UDP server in a new thread."""
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        threading.Thread(target=self.udp_server.start, daemon=True).start()

    def stop_server(self):
        """Stop the UDP server."""
        self.udp_server.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def clear_data(self):
        """Clear the text box displaying received data."""
        self.text_box.delete(1.0, tk.END)  # Clear all text

    def display_received_data(self, data):
        """Display received data in the text box."""
        self.text_box.insert(tk.END, data + "\n")
        self.text_box.yview(tk.END)  # Auto-scroll to the latest data

    def update_status(self, status):
        """Update the status label."""
        self.status_label.config(text=f"Status: {status}")

# Create the main window
root = tk.Tk()
gui = UDPServerGUI(root)

# Run the Tkinter event loop
root.mainloop()