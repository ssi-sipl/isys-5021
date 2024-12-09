import socket
import struct
import threading

class SocketManager:
    def __init__(self, local_ip, local_port, data_callback):
        self.local_ip = local_ip
        self.local_port = local_port
        self.data_callback = data_callback  # Callback to send data to the GUI
        self.socket = None
        self.is_listening = False
        self.thread = None

    def connect(self):
        if not self.is_listening:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.bind((self.local_ip, self.local_port))
                self.is_listening = True
                self.thread = threading.Thread(target=self.listen, daemon=True)
                self.thread.start()
                # print("Listening Started.")
            except Exception as e:
                print(f"Error during connection: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                self.is_listening = False


    def disconnect(self):
        if self.is_listening:
            self.is_listening = False
            if self.socket:
                try:
                    self.socket.close()
                    # print("Socket successfully closed.")
                except Exception as e:
                    print(f"Error closing socket: {e}")
                finally:
                    self.socket = None  # Ensure socket is properly reset
            else:
                print("Socket was already None.")
        else:
            print("Already disconnected.")

    def listen(self):
        while self.is_listening:
            try:
                header_data, _ = self.socket.recvfrom(256)
                data_packet, _ = self.socket.recvfrom(1012)
                self.data_callback(header_data, data_packet)
            except socket.error as e:
                if not self.is_listening:
                    # print("Listening stopped.")
                    break
                print(f"Socket error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")


    def is_connected(self):
        return self.is_listening

    def calculate_checksum(self, data, nrOfTargets, bytesPerTarget):
        target_list = data[4:]
        checksum = 0
        for i in range(nrOfTargets * bytesPerTarget):
            checksum += target_list[i]
            checksum &= 0xFFFFFFFF
        return checksum

    def parse_header(self, data):
        header_format = '<HHHHHHIHH118x'
        header_size = struct.calcsize(header_format)
        
        if len(data) < header_size:
            print("Incomplete header data.")
            return None

        frame_id, fw_major, fw_fix, fw_minor, detections, targets, checksum, bytes_per_target, data_packets = struct.unpack(
            header_format, data[:header_size]
        )
        
        return detections, targets, data_packets, checksum, bytes_per_target

    def parse_data_packet(self, data):
        target_format = '<ffffII'
        target_size = struct.calcsize(target_format)
        
        frame_id, number_of_data_packet = struct.unpack('<HH', data[:4])
        target_list = data[4:]
        
        targets = []
        for i in range(42):
            target_data = target_list[i * target_size:(i + 1) * target_size]
            signal_strength, range_, velocity, azimuth, reserved1, reserved2 = struct.unpack(target_format, target_data)
            
            if signal_strength == 0 and range_ == 0 and velocity == 0 and azimuth == 0:
                continue
            
            
            value_dict = {
                'signal_strength': round(signal_strength, 2),
                'range': round(range_, 2),
                'velocity': round(velocity, 2),
                'azimuth': round(azimuth, 2),
            }
            
            targets.append(value_dict)
            # print("Target Type: ", type(targets))
        
        return frame_id, number_of_data_packet, targets

    def process_packet(self, header_data, data_packet):
        detections, targets, data_packets, expected_checksum, bytes_per_target = self.parse_header(header_data)
        
        if targets is None:
            return  # If header parsing failed, return
        
        

        
        packet_data = header_data + data_packet
        calculated_checksum = self.calculate_checksum(data_packet, targets, bytes_per_target)
        
        if calculated_checksum != expected_checksum:
            return
        else:
            # print(f"Checksum: Okay")
            frame_id, data_packet_number, targets_data = self.parse_data_packet(data_packet)
            return frame_id, targets_data
