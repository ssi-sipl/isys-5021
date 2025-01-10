import math
import datetime
import requests

# Store radar's location globally
radar_latlng = None

# Haversine formula to calculate the distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Returns the distance in meters

def classify_object_by_signal(signal_strength):
    signal_strength = abs(signal_strength)
    if signal_strength > 80:
        return "truck"
    elif 50 <= signal_strength <= 80:
        return "car"
    elif 20 <= signal_strength < 50:
        return "person"
    else:
        return "unknown"

# Radar's location is fetched once and cached
def get_current_location():
    global radar_latlng
    if radar_latlng is None:
        # Fetch the radar location from IPInfo API (once)
        response = requests.get(f'https://ipinfo.io/json?token=c316bcb9bb1ce0')
        if response.status_code == 200:
            # Extract the location data from the response
            data = response.json()
            location = data.get("loc", "0.0,0.0")
            radar_latlng = list(map(float, location.split(',')))
        else:
            radar_latlng = [0.0, 0.0]  # Default if location can't be fetched
    return radar_latlng

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

        # Classify object by signal strength
        obj_class = classify_object_by_signal(signal_strength)
        
        # Calculate the target's latitude and longitude
        azimuth_rad = math.radians(azimuth_deg)
        x = range_m * math.cos(azimuth_rad)
        y = range_m * math.sin(azimuth_rad)
        earth_radius = 6371000  # Earth radius in meters
        
        delta_lat = (y / earth_radius) * (180 / math.pi)
        delta_lon = (x / (earth_radius * math.cos(math.radians(lat_radar)))) * (180 / math.pi)
        
        obj_lat = lat_radar + delta_lat
        obj_lon = lon_radar + delta_lon

        # Calculate distance using Haversine formula
        distance_to_target = haversine(lat_radar, lon_radar, obj_lat, obj_lon)

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
            "distance_to_target": distance_to_target  # Adding the distance to the target
        }
        # print(f"Result: {result}")        
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
