# MQTT Configuration
SEND_MQTT = False
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CHANNEL = "radar_surveillance"
MQTT_BROKER_SUBSCRIBER = "localhost"
MQTT_USERNAME = "rad"
MQTT_PASSWORD = "gxuvimr"

# Serial Port Configuration
SEND_UART = False
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 57600

# Radar Configuration
RADAR_ID = "radar-isys5021"
AREA_ID = "area-1"
RADAR_LAT = 34.011125  # radar latitude
RADAR_LONG = 74.01219  # radar longitude
LOCAL_IP = "192.168.252.2"  # Static IP of the Ethernet
LOCAL_PORT = 2050

# Define thresholds for valid detection - ADJUSTED FOR DEBUGGING
SNR_THRESHOLD = 3
SIGNAL_STRENGTH_THRESHOLD = 15  # Reduced from 18 to 15 for debugging
MIN_SIGNAL_STRENGTH = 10       # Absolute minimum to even consider
MAX_SIGNAL_STRENGTH = 80       # Maximum expected signal strength

# Range and velocity thresholds
MIN_RANGE = 0.5               # Minimum range to avoid near-field effects
MAX_RANGE = 150               # Maximum detection range in meters
MIN_VELOCITY = 0.1            # Minimum velocity to be considered moving
MAX_VELOCITY = 50             # Maximum expected velocity (m/s)

# Angle thresholds
MAX_AZIMUTH = 75              # Maximum azimuth angle in degrees
MIN_AZIMUTH = -75             # Minimum azimuth angle in degrees

# Tracking parameters
TRACK_MAX_DISTANCE = 2.0      # Maximum distance for track association
TRACK_MAX_AGE = 5             # Maximum age for tracks (seconds)
TRACK_HIT_THRESHOLD = 2       # Minimum hits to confirm track
TRACK_MISS_THRESHOLD = 3      # Maximum consecutive misses

# Filtering parameters
ANGLE_JUMP_THRESHOLD = 30     # Maximum angle change per frame (degrees)
VELOCITY_JUMP_THRESHOLD = 5   # Maximum velocity change per frame (m/s)
SIGNAL_STRENGTH_VARIATION = 10 # Expected signal strength variation (dB)

# Debug flags
DEBUG_MODE = True             # Enable debug printing
DEBUG_RAW_DETECTIONS = True   # Print all raw detections
DEBUG_FILTERING = True        # Print filtering decisions
DEBUG_TRACKING = True         # Print tracking decisions
DEBUG_STATISTICS = True       # Print statistics every N frames

# Debug counters
DEBUG_PRINT_INTERVAL = 50     # Print stats every N frames

# Constants
EARTH_R = 6371000             # Earth radius in meters

# Output Configuration
OUTPUT_FILE = "detected_targets.json"
DEBUG_OUTPUT_FILE = "debug_targets.json"
STATS_OUTPUT_FILE = "radar_stats.json"

# Quality thresholds for different object types
QUALITY_THRESHOLDS = {
    'person': {
        'min_signal_strength': 12,
        'min_range': 1.0,
        'max_range': 100,
        'min_velocity': 0.2,
        'max_velocity': 8,
        'expected_rcs': -20  # Typical RCS for person in dBsm
    },
    'vehicle': {
        'min_signal_strength': 15,
        'min_range': 2.0,
        'max_range': 150,
        'min_velocity': 0.5,
        'max_velocity': 30,
        'expected_rcs': -10  # Typical RCS for vehicle in dBsm
    },
    'bicycle': {
        'min_signal_strength': 10,
        'min_range': 1.0,
        'max_range': 80,
        'min_velocity': 0.3,
        'max_velocity': 15,
        'expected_rcs': -25  # Typical RCS for bicycle in dBsm
    },
    'others': {
        'min_signal_strength': 8,
        'min_range': 0.5,
        'max_range': 150,
        'min_velocity': 0.1,
        'max_velocity': 50,
        'expected_rcs': -30  # Generic threshold
    }
}

# Adaptive thresholds based on range
def get_adaptive_signal_threshold(range_m):
    """
    Calculate adaptive signal strength threshold based on range
    Accounts for free space path loss
    """
    if range_m <= 0:
        return MIN_SIGNAL_STRENGTH
    
    # Free space path loss approximation
    # Path loss increases with range
    base_threshold = SIGNAL_STRENGTH_THRESHOLD
    range_factor = 20 * np.log10(range_m / 10)  # Reference at 10m
    
    # Adjust threshold based on range
    adaptive_threshold = base_threshold - range_factor
    
    # Clamp to reasonable bounds
    return max(MIN_SIGNAL_STRENGTH, min(adaptive_threshold, MAX_SIGNAL_STRENGTH))

def get_range_based_velocity_threshold(range_m):
    """
    Get velocity threshold based on range
    Closer objects need higher velocity to be significant
    """
    if range_m < 5:
        return 0.3  # Higher threshold for close objects
    elif range_m < 20:
        return 0.2
    else:
        return 0.1  # Lower threshold for distant objects

# Noise filtering parameters
NOISE_FILTER = {
    'enable': True,
    'velocity_consistency_window': 5,
    'position_consistency_window': 3,
    'signal_strength_consistency_window': 5,
    'outlier_threshold': 2.5  # Standard deviations
}

# Environmental parameters
ENVIRONMENT = {
    'clutter_rejection': True,
    'multipath_mitigation': True,
    'weather_compensation': False,  # Not implemented yet
    'interference_detection': True
}

# Logging configuration
LOGGING = {
    'enable_file_logging': True,
    'log_level': 'DEBUG',  # DEBUG, INFO, WARNING, ERROR
    'log_file': 'radar_debug.log',
    'max_log_size_mb': 100,
    'backup_count': 5
}

# Performance monitoring
PERFORMANCE = {
    'enable_timing': True,
    'timing_window': 100,  # Average over N frames
    'memory_monitoring': True,
    'cpu_monitoring': False
}

# Network configuration
NETWORK = {
    'socket_timeout': 1.0,
    'buffer_size': 2048,
    'retry_attempts': 3,
    'connection_timeout': 5.0
}

# Validation functions
def validate_target(target_dict):
    """
    Validate if a target dictionary contains reasonable values
    """
    checks = {
        'range_valid': MIN_RANGE <= target_dict.get('range', 0) <= MAX_RANGE,
        'velocity_valid': abs(target_dict.get('speed', 0)) <= MAX_VELOCITY,
        'angle_valid': MIN_AZIMUTH <= target_dict.get('aizmuth_angle', 0) <= MAX_AZIMUTH,
        'signal_valid': MIN_SIGNAL_STRENGTH <= target_dict.get('signal_strength', 0) <= MAX_SIGNAL_STRENGTH,
        'position_valid': abs(target_dict.get('x', 0)) <= MAX_RANGE and abs(target_dict.get('y', 0)) <= MAX_RANGE
    }
    
    return all(checks.values()), checks

def print_config_summary():
    """Print configuration summary for debugging"""
    print("=== RADAR CONFIGURATION SUMMARY ===")
    print(f"Signal Strength Threshold: {SIGNAL_STRENGTH_THRESHOLD} dB")
    print(f"Range: {MIN_RANGE} - {MAX_RANGE} m")
    print(f"Velocity: {MIN_VELOCITY} - {MAX_VELOCITY} m/s")
    print(f"Azimuth: {MIN_AZIMUTH}° - {MAX_AZIMUTH}°")
    print(f"Tracking Distance: {TRACK_MAX_DISTANCE} m")
    print(f"Debug Mode: {DEBUG_MODE}")
    print("=====================================")

# Import numpy for adaptive functions
import numpy as np

if __name__ == "__main__":
    print_config_summary()