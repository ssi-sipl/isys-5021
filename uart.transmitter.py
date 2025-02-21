import serial
import json
import time

# --- CONFIGURATION ---
SERIAL_PORT = "/dev/ttyUSB0"  # Change if necessary
BAUD_RATE = 57600  # Must match receiver settings

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

frame_id = 0

while True:
    # Sample detection data
    detection_data = {
        "radar_id": 1,
        "frame_id": frame_id,
        "speed": round(10 + (frame_id % 5) * 2.5, 2),
        "classification": "vehicle",
        "latitude": 22.7196 + (frame_id % 10) * 0.0001,
        "longitude": 75.8577 + (frame_id % 10) * 0.0001
    }

    json_data = json.dumps(detection_data)
    ser.write((json_data + "\n").encode('utf-8'))  # Send JSON with newline
    print(f"[Transmitter] Sent: {json_data}")

    frame_id += 1
    time.sleep(1)  # Adjust transmission rate
