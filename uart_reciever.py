import serial
import json

# --- CONFIGURATION ---
SERIAL_PORT = "/dev/ttyUSB0"  # Change if necessary
BAUD_RATE = 57600  # Must match transmitter settings

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def subscriber():
    while True:
        if ser.in_waiting > 0:  # Check if data is available
            received_message = ser.readline().decode('utf-8').strip()
            if received_message:
                try:
                    data = json.loads(received_message)  # Parse JSON
                    print(f"Received: {data}")
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {received_message}")

if __name__ == "__main__":
    try:
        subscriber()
    except KeyboardInterrupt:
        print("Subscriber stopped.")
