import socket
import tkinter as tk
from tkinter import scrolledtext
import threading

# Configuration
local_ip = "192.168.252.2"  # IP to listen on
local_port = 2050  # Port to listen on
buffer_size = 1024  # Adjust as needed

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
    
    def receive_data(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(buffer_size)
                # Handle data
                if addr[0] == "192.168.252.10" and addr[1] == 2051:
                    # Decode or print raw data
                    try:
                        decoded_data = data.decode('utf-8')
                        self.gui.display_received_data(f"Received from {addr}: {decoded_data}")
                    except UnicodeDecodeError:
                        self.gui.display_received_data(f"Non-UTF-8 data from {addr}: {data}")
            except Exception as e:
                if self.running:  # Handle exception only if the server is still running
                    self.gui.display_received_data(f"Error: {e}")
                break

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

    def display_received_data(self, data):
        self.text_box.insert(tk.END, data + "\n")
        self.text_box.yview(tk.END)  # Auto-scroll to the latest data

    def update_status(self, status):
        self.status_label.config(text=f"Status: {status}")

# Create the main window"
root = tk.Tk()
gui = UDPServerGUI(root)

# Run the Tkinter event loop
root.mainloop()
