# MQTT Configuration
SEND_MQTT = False
MQTT_BROKER = "localhost"  # Change to your broker's IP address if needed
MQTT_PORT = 1883
MQTT_CHANNEL = "radar_surveillance"
MQTT_BROKER_SUBSCRIBER = "localhost" # Change to your broker's IP address
MQTT_USERNAME = "rad"
MQTT_PASSWORD = "gxuvimr"

# Serial Port Configuration
SEND_UART = False
SERIAL_PORT = "/dev/ttyUSB0"  # Change if necessary
BAUD_RATE = 57600  # Must match receiver settings

SEND_WEBSOCKET = False

# Radar Configuration
RADAR_ID = "radar-isys5021"
AREA_ID = "area-1"
RADAR_LAT = 34.011125  #  radar latitude
RADAR_LONG = 74.01219  #  radar longitude
LOCAL_IP = "192.168.252.2" # Static IP of the Ethernet
LOCAL_PORT = 2050

# Tracker Configuration
RANGE_THRESHOLD = 1.0      # meters
AZIMUTH_THRESHOLD = 5.0   # degrees
MAX_MISSED_FRAMES = 5  # Maximum missed frames before track is removed

# Define thresholds for valid detection
MIN_SIGNAL_STRENGTH = 4  # Minimum valid signal strength (in dB)
MAX_SIGNAL_STRENGTH = 100  # Maximum valid signal strength (in dB)

# Features ( if both are false, all targets will be detected )
DETECT_ONLY_STATIC = False  # Only detect static targets
DETECT_ONLY_MOVING = False  # Only detect moving targets
PERSON_ONLY = False

DEBUG_MODE = True  # Enable debug mode for data logging

# constants
EARTH_R = 6371000 # Earth radius in meters

# Output Configuration
OUTPUT_FILE = "FINALDATA.json"

# Basic Information
MAX_RANGE = 150  # Maximum detection range in meters
MAX_AZIMUTH = 75  # Maximum azimuth angle in degrees
