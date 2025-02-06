#MQTT Configuration
SEND_MQTT = False
MQTT_BROKER = "localhost"  # Change to your broker's IP address if needed
MQTT_PORT = 1883
MQTT_CHANNEL = "radar_surveillance"
MQTT_BROKER_SUBSCRIBER = "localhost" # Change to your broker's IP address
MQTT_USERNAME = ""
MQTT_PASSWORD = ""


# Radar Configuration
RADAR_ID = "radar-isys5021"
AREA_ID = "area-1"
RADAR_LAT = 34.011125  #  radar latitude
RADAR_LONG = 74.01219  #  radar longitude

LOCAL_IP = "192.168.252.2" # Static IP of the Ethernet
LOCAL_PORT = 2050

# Defii

# constants
EARTH_R = 6371000 # Earth radius in meters

# Output Configuration
OUTPUT_FILE = "detected_targets.json"

# Basic Information
MAX_RANGE = 150  # Maximum detection range in meters
MAX_AZIMUTH = 75  # Maximum azimuth angle in degrees
