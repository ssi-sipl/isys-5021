import matplotlib.pyplot as plt
import numpy as np

# Radar parameters
max_range = 150  # Maximum detection range in meters
max_azimuth = 75  # Maximum azimuth angle in degrees

# Example radar data (in the form of a list of dicts)
radar_data = [
    {"frame_id": 30639, "x": 2.81, "y": -0.6, "range": 2.88, "azimuth": -12.0},
    {"frame_id": 30641, "x": 2.81, "y": -0.6, "range": 2.88, "azimuth": -12.0},
    {"frame_id": 30643, "x": 2.82, "y": -0.6, "range": 2.88, "azimuth": -12.0},
    {"frame_id": 30645, "x": 2.82, "y": -0.6, "range": 2.89, "azimuth": -12.0}
]

# Convert radar data from polar to Cartesian coordinates
targets = []
for data in radar_data:
    range_ = data["range"]
    azimuth = data["azimuth"]
    
    # Convert polar coordinates to Cartesian coordinates (x, y)
    x = range_ * np.cos(np.radians(azimuth))
    y = range_ * np.sin(np.radians(azimuth))
    targets.append((x, y))

# Create a figure and axis
plt.figure(figsize=(8, 8))
ax = plt.subplot(111, projection='polar')

# Plot the radar's detection area
theta = np.linspace(-np.radians(max_azimuth), np.radians(max_azimuth), 100)
r = np.full_like(theta, max_range)
ax.fill(theta, r, color='lightblue', alpha=0.3)

# Plot the targets in the radar detection area
for target in targets:
    azimuth = np.degrees(np.arctan2(target[1], target[0]))  # Calculate azimuth
    range_ = np.hypot(target[0], target[1])  # Calculate range
    if -max_azimuth <= azimuth <= max_azimuth and range_ <= max_range:
        ax.scatter(np.radians(azimuth), range_, color='red', label="Detected Target")

# Customize the plot
ax.set_rticks([20, 40, 60, 80, 100, 120, 140])  # Range ticks
ax.set_rlabel_position(-22.5)  # Labels for range
ax.set_xlabel("Azimuth Angle (Degrees)")
ax.set_ylabel("Range (meters)")
ax.set_title(f"Radar Detection Area (Azimuth: ±{max_azimuth}°, Range: {max_range}m)")

# Show plot
plt.show()
