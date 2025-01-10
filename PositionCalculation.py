import math
import datetime
import requests

# Store radar's location globally
radar_latlng = None

def classify_object_by_signal(signal_strength):
    signal_strength = abs(signal_strength)
    if signal_strength > 50:  # Objects with high signal strength
        return "truck"
    elif 30 <= signal_strength <= 50:  # Medium signal strength
        return "car"
    elif 10 <= signal_strength < 30:  # Weak signal strength, maybe a person
        return "person"
    else:
        return "unknown"

def get_current_location():
    try:
        global radar_latlng
        if radar_latlng is None:
            # Send request to IPInfo API with your API key
            response = requests.get(f'https://ipinfo.io/json?token=c316bcb9bb1ce0')
            if response.status_code == 200:
                # Extract the location data from the response
                data = response.json()
                location = data.get("loc", "0.0,0.0")
                lat, lon = map(float, location.split(','))
                return [lat, lon]
            else:
                print("Failed to fetch location")
                return [0.0, 0.0]  # Default if location can't be fetched
        return radar_latlng
    except Exception as e:
        print(f"Error fetching location: {e}")
        return [0.0, 0.0]  # Default if there's an error

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth's surface."""
    # Radius of the Earth in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c * 1000  # Return distance in meters

def parse_isys5021_data(data, radar_id="iSYS5021", area_id="Zone A"):
    try:
        lat_radar, lon_radar = get_current_location()
        frame_id = data.get("frameid")
        range_m = data.get("range")
        azimuth_deg = data.get("azimuth")
        signal_strength = data.get("signal_strength")
        timestamp = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

        if range_m is None or azimuth_deg is None or signal_strength is None:
            raise ValueError("Missing required fields: 'range', 'azimuth', or 'signal_strength'.")

        # Normalize azimuth to [0, 360]
        azimuth_deg = azimuth_deg % 360

        obj_class = classify_object_by_signal(signal_strength)

        # Updated latitude and longitude calculation
        azimuth_rad = math.radians(azimuth_deg)
        x = range_m * math.cos(azimuth_rad)
        y = range_m * math.sin(azimuth_rad)
        earth_radius = 6371000  # Earth's radius in meters

        # Calculate the change in latitude and longitude
        delta_lat = (y / earth_radius) * (180 / math.pi)
        delta_lon = (x / (earth_radius * math.cos(math.radians(lat_radar)))) * (180 / math.pi)

        # Calculate target's latitude and longitude
        obj_lat = lat_radar + delta_lat
        obj_lon = lon_radar + delta_lon

        # Calculate the distance from the radar to the detected target
        distance_to_target = haversine_distance(lat_radar, lon_radar, obj_lat, obj_lon)

        result = {
            "radar_id": radar_id,
            "area_id": area_id,
            "timestamp": timestamp,
            "object_detected": True,
            "classification": obj_class,
            "latitude": obj_lat,
            "longitude": obj_lon,
            "frame_id": frame_id,
            "range": range_m,
            "azimuth": azimuth_deg,
            "signal_strength": signal_strength,
            "distance_to_target": distance_to_target
        }
        return result

    except Exception as e:
        print(f"Error in parsing data: {e}")
        return {
            "radar_id": radar_id,
            "area_id": area_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "object_detected": False,
            "classification": "unknown",
            "latitude": None,
            "longitude": None,
            "frame_id": data.get("frameid"),
            "range": data.get("range"),
            "azimuth": data.get("azimuth"),
            "signal_strength": data.get("signal_strength"),
            "distance_to_target": None
        }

# Example usage
if __name__ == "__main__":
    data_input_150m = {
        "frameid": 101,
        "range": 100,
        "azimuth": 45,
        "signal_strength": 75,
        "timestamp": "2025-01-06T12:50:30Z"
    }

    parsed_data_150m = parse_isys5021_data(data_input_150m)
    print(parsed_data_150m)
