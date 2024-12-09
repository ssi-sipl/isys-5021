import tkinter as tk
from tkinter import ttk, filedialog
from socket_manager import SocketManager
from data_manager import DataManager
import struct
import json

class RadarApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("150M DATA PARSER (ISYS 5021)")
        self.data_manager = DataManager()
        self.socket_manager = SocketManager("192.168.252.2", 2050, self.process_data)
        self.build_gui()

    def build_gui(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Connect Button
        self.connect_btn = tk.Button(button_frame, bg="green", fg="white", text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # Clear Button
        self.clear_btn = tk.Button(button_frame, text="Clear", command=self.clear_display)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Save JSON Button
        self.save_btn = tk.Button(button_frame, text="Save to JSON", command=self.save_to_json)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Add Label above Frame ID Dropdown
        self.frame_history_label = tk.Label(button_frame, text="Frame History")
        self.frame_history_label.pack(side=tk.LEFT, padx=5)

        # Frame ID Dropdown
        self.frame_id_var = tk.StringVar()
        self.frame_id_dropdown = ttk.Combobox(button_frame, textvariable=self.frame_id_var)
        self.frame_id_dropdown.bind("<<ComboboxSelected>>", self.display_by_frame_id)
        self.frame_id_dropdown.pack(side=tk.LEFT, padx=5)

        # Data Display
        self.text_display = tk.Text(self.root, height=20, width=80)
        self.text_display.pack()

    def toggle_connection(self):
        if self.socket_manager.is_connected():
            try:
                self.socket_manager.disconnect()
                self.update_display("\nStopped listening for data from the Radar", "red")
                self.connect_btn.config(text="Connect", bg="green", fg="white")
            except Exception as e:
                self.update_display("\nThere was some error disconnecting from the Radar", "red")
                print(f"Error during disconnection: {e}")
        else:
            try:
                self.socket_manager.connect()
                self.update_display("\nListening for data from the Radar", "green")
                self.connect_btn.config(text="Disconnect", bg="red", fg="white")
            except Exception as e:
                self.update_display("\nThere was some error connecting to the Radar", "red")
                print(f"Error during connection: {e}")

    def update_display(self, message, color):
        """Update the text display with a colored message."""
        self.text_display.tag_configure(color, foreground=color)
        self.text_display.insert(tk.END, message + "\n", color)
        self.text_display.see(tk.END)

    def clear_display(self):
        self.text_display.delete(1.0, tk.END)

    def save_to_json(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            self.data_manager.save_to_json(filename)

    def display_by_frame_id(self, event):
        frame_id = self.frame_id_var.get()

        # print(f"Selected Frame ID: {frame_id}")
        serials = self.data_manager.get_by_frame_id(frame_id)
        
        # Debugging: Check the format of serials
        # print(f"Retrieved Serial Data: {serials}")  # Should print a list of dictionaries

        self.clear_display()

        if serials:
            self.text_display.insert(tk.END, f"Serial Data for Frame ID: {frame_id}\n")
            self.text_display.insert(tk.END, "-" * 50 + "\n")
            
            for idx, target in enumerate(serials, start=1):
                
                direction = "Static" if target["velocity"] == 0 else "Incoming" if target["velocity"] > 0 else "Outgoing"
                self.text_display.insert(tk.END, f"\nFrame ID: {frame_id}\n"f"Serial {idx}: \n"
                                             f"Signal Strength: {target['signal_strength']} dB\n"
                                             f"Range: {target['range']} m\n"
                                             f"Velocity: {target['velocity']} m/s\n"
                                             f"Direction: {direction}\n"
                                             f"Azimuth: {target['azimuth']}°\n")
                
            self.text_display.insert(tk.END, "-" * 50 + "\n")
        else:
            self.text_display.insert(tk.END, "No serial data available for this Frame ID.\n")

    def process_data(self, header_data, data_packet):
        frame_id, targets = self.socket_manager.process_packet(header_data, data_packet)
        if not targets:
            return
        
        

        self.data_manager.save_packet(frame_id, targets)
        # print(f"Updated history: {self.data_manager.history}")
        self.frame_id_dropdown['values'] = list(self.data_manager.history.keys())
        self.clear_display()
        self.text_display.insert(tk.END, f"\n{'-' * 10}FRAME START{'-' * 10}")
        for idx, target in enumerate(targets, start=1):
            direction = "Static" if target["velocity"] == 0 else "Incoming" if target["velocity"] > 0 else "Outgoing"
            self.text_display.insert(tk.END, f"\nFrame ID: {frame_id}\n"f"Serial {idx}: \n"
                                             f"Signal Strength: {target['signal_strength']} dB\n"
                                             f"Range: {target['range']} m\n"
                                             f"Velocity: {target['velocity']} m/s\n"
                                             f"Direction: {direction}\n"
                                             f"Azimuth: {target['azimuth']}°\n")
        self.text_display.insert(tk.END, f"\n{'-' * 10}FRAME END{'-' * 10}")

    def run(self):
        self.root.mainloop()
