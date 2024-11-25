import socket
import tkinter as tk
from tkinter import scrolledtext, filedialog
import threading
import struct  # For binary data unpacking

# Configuration
local_ip = "192.168.252.2"  # IP to listen on
local_port = 2050  # Port to listen on
buffer_size = 2048  # Adjusted to accommodate larger packets

# UDP server class
class UDPServer:
    def __init__(self, ip, port, gui):
        self.ip = ip
        self.port = port
        self.gui = gui
        self.running = False
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def start(self):
        self.udp_socket.bind((self.ip, self.port))
        self.running = True
        self.gui.update_status("Server running...")
        self.receive_data()

    def stop(self):
        self.running = False
        self.udp_socket.close()
        self.gui.update_status("Server stopped.")
    
    def calculate_checksum(self, target_data):
        """Calculate checksum as a byte-wise XOR over all target data."""
        checksum = 0
        for byte in target_data:
            checksum ^= byte
        return checksum

    def decode_data(self, data):
        # Header format as described in the document
        header_format = '<HBBBHHBB240x'  # Matches the header structure in little-endian
        header_size = struct.calcsize(header_format)
        
        if len(data) < header_size:
            return "Insufficient data for header."

        # Unpack the header
        header = struct.unpack(header_format, data[:header_size])
        frameID, FWmajor, FWminor, FWfix, nrOfDetections, nrOfTargets, crc, bytesPerTarget = header
        
        # Header information as a string
        header_info = (f"Frame ID: {frameID}\n"
                       f"Firmware Version: {FWmajor}.{FWminor}.{FWfix}\n"
                       f"Number of Detections: {nrOfDetections}\n"
                       f"Number of Targets: {nrOfTargets}\n"
                       f"Checksum (from header): {crc}\n"
                       f"Bytes per Target: {bytesPerTarget}\n")
        
        # Check if there is sufficient data for the target list
        if len(data) < header_size + nrOfTargets * bytesPerTarget:
            return header_info + "Insufficient data for targets."

        # Process target data
        target_format = '<fffff'  # Each target: signalStrength, range, velocity, azimuth, elevation
        target_size = struct.calcsize(target_format)
        targets_info = ""

        target_data_start = header_size
        target_data_end = header_size + (nrOfTargets * target_size)
        target_data = data[target_data_start:target_data_end]

        # Verify checksum
        calculated_crc = self.calculate_checksum(target_data)
        if calculated_crc != crc:
            return header_info + f"Checksum mismatch! Calculated: {calculated_crc}, Expected: {crc}\n"

        # Decode each target
        for i in range(nrOfTargets):
            target_start = i * target_size
            target_end = target_start + target_size
            target = struct.unpack(target_format, target_data[target_start:target_end])

            signalStrength, range_, velocity, azimuth, elevation = target
            targets_info += (f"Target {i+1}:\n"
                             f"  Signal Strength: {signalStrength}\n"
                             f"  Range: {range_} meters\n"
                             f"  Velocity: {velocity} m/s\n"
                             f"  Azimuth: {azimuth} degrees\n"
                             f"  Elevation: {elevation} degrees\n")

        return header_info + targets_info

    def receive_data(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(buffer_size)
                # Decode the received data only if from expected sender
                if addr[0] == "192.168.252.10" and addr[1] == 2051:
                    translated_data = self.decode_data(data)
                    self.gui.display_received_data(f"Received from {addr}:\n{translated_data}")
            except Exception as e:
                if self.running:  # Handle exception only if the server is still running
                    self.gui.display_received_data(f"Error: {e}")
                break

# GUI for the UDP server
class UDPServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP Server")

        # Create text box to display received data
        self.text_box = scrolledtext.ScrolledText(root, width=70, height=25)
        self.text_box.pack(padx=10, pady=10)

        # Create status label
        self.status_label = tk.Label(root, text="Status: Stopped", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)

        # Create buttons
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_button.pack(side="left", padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_button.pack(side="left", padx=10, pady=10)

        self.clear_button = tk.Button(root, text="Clear", command=self.clear_text)
        self.clear_button.pack(side="left", padx=10, pady=10)

        self.save_button = tk.Button(root, text="Save", command=self.save_to_file)
        self.save_button.pack(side="left", padx=10, pady=10)

        # Create UDP server instance
        self.udp_server = UDPServer(local_ip, local_port, self)

    def start_server(self):
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        threading.Thread(target=self.udp_server.start, daemon=True).start()

    def stop_server(self):
        self.udp_server.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def clear_text(self):
        """Clear the text box."""
        self.text_box.delete(1.0, tk.END)

    def save_to_file(self):
        """Save received data to a file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_box.get(1.0, tk.END))

    def display_received_data(self, data):
        self.text_box.insert(tk.END, data + "\n")
        self.text_box.yview(tk.END)

    def update_status(self, status):
        self.status_label.config(text=f"Status: {status}")

# Main application
root = tk.Tk()
gui = UDPServerGUI(root)
root.mainloop()