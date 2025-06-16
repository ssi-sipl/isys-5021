import numpy as np
from scipy.spatial import distance
from filterpy.kalman import KalmanFilter
import uuid
import time
from datetime import datetime, timedelta
from config import *
import math

class RadarTarget:
    def __init__(self, target_info, track_id=None):
        # Initialize target with detection data
        self.id = track_id if track_id else str(uuid.uuid4())[:8]
        self.first_detection = target_info
        self.last_detection = target_info
        self.detection_history = [target_info]
        self.last_update_time = time.time()
        self.consecutive_misses = 0
        self.classified_as = target_info['classification']
        self.classification_history = [target_info['classification']]
        self.classification_counts = {target_info['classification']: 1}
        
        # Initialize Kalman filter
        self.kf = self._initialize_kalman_filter(target_info)
        
    def _initialize_kalman_filter(self, detection):
        """Initialize Kalman filter with 6 state variables (x, y, vx, vy, ax, ay)"""
        kf = KalmanFilter(dim_x=6, dim_z=2)
        
        # State transition matrix (position + velocity + acceleration model)
        dt = 0.1  # 100ms update rate from radar
        kf.F = np.array([
            [1, 0, dt, 0, 0.5*dt**2, 0],
            [0, 1, 0, dt, 0, 0.5*dt**2],
            [0, 0, 1, 0, dt, 0],
            [0, 0, 0, 1, 0, dt],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement function (we only measure position x,y)
        kf.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0]
        ])
        
        # Measurement noise
        kf.R = np.array([
            [5.0, 0],
            [0, 5.0]
        ])
        
        # Process noise
        q = 0.001  # process noise
        kf.Q = np.array([
            [q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2, 0],
            [0, q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2],
            [q/2*dt**3, 0, q*dt**2, 0, q*dt, 0],
            [0, q/2*dt**3, 0, q*dt**2, 0, q*dt],
            [q/2*dt**2, 0, q*dt, 0, q, 0],
            [0, q/2*dt**2, 0, q*dt, 0, q]
        ])
        
        # Initial state
        kf.x = np.array([
            [detection['x']],
            [detection['y']],
            [detection['speed'] * np.cos(np.radians(detection['aizmuth_angle']))],
            [detection['speed'] * np.sin(np.radians(detection['aizmuth_angle']))],
            [0],
            [0]
        ]).reshape(6, 1)
        
        # Initial covariance
        kf.P = np.eye(6) * 50
        
        return kf
    
    # def update(self, detection):
    #     """Update target with new detection"""
    #     # Update Kalman filter
    #     z = np.array([detection['x'], detection['y']])
    #     self.kf.predict()
    #     self.kf.update(z)
        
    #     # Update target properties
    #     self.last_detection = detection
    #     self.detection_history.append(detection)
    #     self.last_update_time = time.time()
    #     self.consecutive_misses = 0
        
    #     # Update classification
    #     self.classification_history.append(detection['classification'])
    #     if detection['classification'] in self.classification_counts:
    #         self.classification_counts[detection['classification']] += 1
    #     else:
    #         self.classification_counts[detection['classification']] = 1
            
    #     # Update most frequent classification
    #     self.classified_as = max(self.classification_counts, key=self.classification_counts.get)

    def update(self, detection):
        """Update target with new detection"""
        # Update Kalman filter
        z = np.array([detection['x'], detection['y']])
        self.kf.predict()
        self.kf.update(z)

        # Update target properties
        self.last_detection = detection
        self.detection_history.append(detection)
        self.last_update_time = time.time()
        self.consecutive_misses = 0

        # Update classification
        self.classification_history.append(detection['classification'])
        self.classification_counts[detection['classification']] = self.classification_counts.get(detection['classification'], 0) + 1

        # Update most frequent classification
        self.classified_as = max(self.classification_counts, key=self.classification_counts.get)

        # Ensure signal strength is updated
        if 'signal_strength' in detection:
            self.last_detection['signal_strength'] = detection['signal_strength']

    
    def predict(self):
        """Predict next position without measurement update"""
        self.kf.predict()
        return self.get_predicted_position()
    
    def get_predicted_position(self):
        """Get predicted position"""
        x, y = self.kf.x[0, 0], self.kf.x[1, 0]
        vx, vy = self.kf.x[2, 0], self.kf.x[3, 0]
        speed = np.sqrt(vx**2 + vy**2)
        
        # Calculate azimuth from velocity vector
        azimuth = np.degrees(np.arctan2(vy, vx))
        range_val = np.sqrt(x**2 + y**2)

        print("Raw azimuth:", self.last_detection['aizmuth_angle'], "→ Computed azimuth:", azimuth)

        
        return {
            'x': x,
            'y': y,
            'speed': speed,
            'aizmuth_angle': azimuth,
            'range': range_val
        }
    
    def get_state(self):
        """Get current state as dict with tracking info"""
        state = self.last_detection.copy()
        
        # Update with Kalman filter state
        predicted = self.get_predicted_position()
        state.update({
            'track_id': self.id,
            'x': predicted['x'],
            'y': predicted['y'],
            'speed': predicted['speed'],
            'aizmuth_angle': predicted['aizmuth_angle'],
            'range': predicted['range'],
            'tracked_classification': self.classified_as,
            'age': len(self.detection_history),
            'last_seen': time.time() - self.last_update_time
        })
        
        return state

class RadarTracker:
    def __init__(self, max_distance=0.5, max_age=2, hit_threshold=3):
        """
        Initialize tracker
        
        Args:
            max_distance: Maximum distance for track association (meters)
            max_age: Maximum time without update before removing track (seconds)
            hit_threshold: Minimum detections before track is considered confirmed
        """
        self.tracks = []
        self.max_distance = max_distance
        self.max_age = max_age
        self.hit_threshold = hit_threshold
        self.next_id = 1
    
    def update(self, detections):
        """Update tracker with new detections"""
        # Predict new locations for all tracks
        for track in self.tracks:
            track.predict()
        
        # Associate detections with existing tracks
        unmatched_detections = self._associate_detections_to_tracks(detections)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            self.tracks.append(RadarTarget(detection))
        
        # Remove old tracks
        self._cleanup_tracks()
        
        # Return current tracks
        return self.get_tracks()
    
    def _associate_detections_to_tracks(self, detections):
        """Associate detections with existing tracks using nearest neighbor approach"""
        if not self.tracks:
            return detections
        
        if not detections:
            # No detections, increment consecutive misses for all tracks
            for track in self.tracks:
                track.consecutive_misses += 1
            return []
        
        # Calculate distance matrix
        distance_matrix = np.zeros((len(self.tracks), len(detections)))
        
        for i, track in enumerate(self.tracks):
            predicted = track.get_predicted_position()
            for j, detection in enumerate(detections):
                # Calculate Euclidean distance
                dist = np.sqrt((predicted['x'] - detection['x'])**2 + 
                              (predicted['y'] - detection['y'])**2)
                distance_matrix[i, j] = dist
        
        # Associate using greedy nearest neighbor
        matched_detections = set()
        unmatched_detections = []
        
        # For each track, find nearest detection
        for i, track in enumerate(self.tracks):
            if len(detections) == 0:
                track.consecutive_misses += 1
                continue
                
            # Get detections sorted by distance
            detection_distances = [(j, distance_matrix[i, j]) for j in range(len(detections))]
            detection_distances.sort(key=lambda x: x[1])
            
            # Try to match with closest detection
            for j, dist in detection_distances:
                if j not in matched_detections and dist <= self.max_distance:
                    track.update(detections[j])
                    matched_detections.add(j)
                    break
            else:
                # No match found
                track.consecutive_misses += 1
        
        # Collect unmatched detections
        for j, detection in enumerate(detections):
            if j not in matched_detections:
                unmatched_detections.append(detection)
        
        return unmatched_detections
    
    def _cleanup_tracks(self):
        """Remove old tracks"""
        current_time = time.time()
        self.tracks = [track for track in self.tracks 
                      if (current_time - track.last_update_time < self.max_age and 
                          track.consecutive_misses < 5)]
    
    def get_tracks(self):
        """Get list of current tracks"""
        return [track.get_state() for track in self.tracks 
                if len(track.detection_history) >= self.hit_threshold]

# Function to integrate with your existing code
def process_and_track_targets(targets, tracker):
    """
    Process radar targets and update tracker
    
    Args:
        targets: List of target dictionaries
        tracker: RadarTracker instance
    
    Returns:
        List of tracked objects with IDs and predicted states
    """
    # Update tracker with new detections
    tracked_targets = tracker.update(targets)
    
    filtered_targets = []
    # Add tracking-related info to each target
    for target in tracked_targets:
        # Calculate additional metrics if needed
        if abs(target['speed']) > 0.2 and target['signal_strength'] > SIGNAL_STRENGTH_THRESHOLD:  # If moving
            # Predict position in 2 seconds
            x_future = target['x'] + 2 * target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
            y_future = target['y'] + 2 * target['speed'] * np.sin(np.radians(target['aizmuth_angle']))
            target['predicted_x'] = x_future
            target['predicted_y'] = y_future
            # target['aizmuth_angle'] = max(-75, min(target['aizmuth_angle'], 75)) # keep the azimuth in range
            
            # Calculate time to closest approach (TCA) for targets moving toward radar
            # TCA is useful for collision avoidance or alerting
            if abs(target['speed']) > 0 and target['range'] > 0:
                # Radial velocity component
                v_radial = target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
                if v_radial < 0:  # Target is approaching
                    tca = -target['range'] / v_radial if v_radial != 0 else float('inf')
                    target['time_to_closest_approach'] = round(tca, 2)  # in seconds
            # print("FROM PROCESS TRACK TARGETS: ", target)
            filtered_targets.append(target)
    
    return filtered_targets