import matplotlib.pyplot as plt

# Data for plotting (x, y positions of detected targets)
detected_targets = [
    {"frame_id": 30639, "x": 2.81, "y": -0.6},
    {"frame_id": 30641, "x": 2.81, "y": -0.6},
    {"frame_id": 30643, "x": 2.82, "y": -0.6},
    {"frame_id": 30645, "x": 2.82, "y": -0.6}
]

# Extract x and y coordinates for plotting
x_coords = [target["x"] for target in detected_targets]
y_coords = [target["y"] for target in detected_targets]

# Plot the data
plt.figure(figsize=(8, 6))
plt.scatter(x_coords, y_coords, c='blue', label="Detected Targets", s=100, edgecolors='black')

# Labels and title
plt.title("Radar Data: Detected Targets", fontsize=16)
plt.xlabel("X Position (m)", fontsize=14)
plt.ylabel("Y Position (m)", fontsize=14)

# Display frame IDs as annotations
for i, target in enumerate(detected_targets):
    plt.annotate(f"Frame ID: {target['frame_id']}", (x_coords[i] + 0.02, y_coords[i] + 0.02), fontsize=10)

# Show grid and legend
plt.grid(True)
plt.legend()

# Show the plot
plt.show()
