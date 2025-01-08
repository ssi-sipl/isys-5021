import math
import datetime

def parse_isys5021_data(data, radar_id="iSYS5021", area_id="Zone A", lat_radar=22.345678, lon_radar=73.123456):
    try:
        range_m = data.get("range")
        azimuth_deg = data.get("azimuth")
        obj_class = data.get("classification")
        timestamp = data.get("timestamp", datetime.datetime.utcnow().isoformat() + "Z")

        if range_m is None or azimuth_deg is None or obj_class is None:
            raise ValueError("Missing required fields: 'range', 'azimuth', or 'classification'.")

        if not (0 <= azimuth_deg <= 360):
            raise ValueError("Azimuth angle must be between 0 and 360 degrees.")
        
        # Convert azimuth to radians
        azimuth_rad = math.radians(azimuth_deg)
        
        # Calculate (x, y) coordinates relative to the radar
        x = range_m * math.cos(azimuth_rad)
        y = range_m * math.sin(azimuth_rad)
        
        # Earth's radius in meters
        earth_radius = 6371000
        
        # Convert (x, y) to latitude and longitude offsets
        delta_lat = (y / earth_radius) * (180 / math.pi)
        delta_lon = (x / (earth_radius * math.cos(math.radians(lat_radar)))) * (180 / math.pi)
        
        # Calculate the object's absolute latitude and longitude
        obj_lat = lat_radar + delta_lat
        obj_lon = lon_radar + delta_lon
        
        result = {
            "radar_id": radar_id,
            "area_id": area_id,
            "timestamp": timestamp,
            "object_detected": True,
            "classification": obj_class,
            "latitude": obj_lat,
            "longitude": obj_lon
        }
        return result

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return None
    except KeyError as ke:
        print(f"KeyError: {ke}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Example usage
data_input_150m = {
    "frameid": 101,
    "range": 100,
    "azimuth": 45,
    "classification": "car",
    "timestamp": "2025-01-06T12:50:30Z"
}

parsed_data_150m = parse_isys5021_data(data_input_150m)
print(parsed_data_150m)
