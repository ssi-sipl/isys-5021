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
        
        # Angle tracking for jump detection
        self.angle_history = [target_info['aizmuth_angle']]
        self.last_valid_angle = target_info['aizmuth_angle']
        
        # Velocity tracking for consistency
        self.velocity_history = [target_info.get('velocity_raw', target_info['speed'])]
        
        # Initialize Kalman filter
        self.kf = self._initialize_kalman_filter(target_info)
        
    def _initialize_kalman_filter(self, detection):
        """Initialize Kalman filter with 6 state variables (x, y, vx, vy, ax, ay)"""
        kf = KalmanFilter(dim_x=6, dim_z=2)
        
        # State transition matrix (constant velocity model with some acceleration)
        dt = 0.1  # 100ms update rate from radar
        kf.F = np.array([
            [1, 0, dt, 0, 0.5*dt**2, 0],
            [0, 1, 0, dt, 0, 0.5*dt**2],
            [0, 0, 1, 0, dt, 0],
            [0, 0, 0, 1, 0, dt],
            [0, 0, 0, 0, 0.8, 0],  # Damping factor for acceleration
            [0, 0, 0, 0, 0, 0.8]
        ])
        
        # Measurement function (we only measure position x,y)
        kf.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0]
        ])
        
        # Measurement noise - adjusted for radar characteristics
        kf.R = np.array([
            [2.0, 0],    # Reduced noise for better tracking
            [0, 2.0]
        ])
        
        # Process noise - reduced for more stable tracking
        q = 0.1
        kf.Q = np.array([
            [q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2, 0],
            [0, q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2],
            [q/2*dt**3, 0, q*dt**2, 0, q*dt, 0],
            [0, q/2*dt**3, 0, q*dt**2, 0, q*dt],
            [q/2*dt**2, 0, q*dt, 0, q, 0],
            [0, q/2*dt**2, 0, q*dt, 0, q]
        ])
        
        # Initial velocity calculation
        vel_rad = np.radians(detection['aizmuth_angle'])
        vx = detection['speed'] * np.cos(vel_rad)
        vy = detection['speed'] * np.sin(vel_rad)
        
        # Initial state
        kf.x = np.array([
            detection['x'],
            detection['y'],
            vx,
            vy,
            0,  # Initial acceleration
            0
        ]).reshape(6, 1)
        
        # Initial covariance - more conservative
        kf.P = np.eye(6) * 10
        
        return kf
    
    def _detect_angle_jump(self, new_angle, threshold=30):
        """Detect if angle has jumped unrealistically"""
        if len(self.angle_history) < 2:
            return False
            
        # Calculate angle difference considering wrapping
        angle_diff = abs(new_angle - self.last_valid_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
            
        # Check if jump is too large
        return angle_diff > threshold
    
    def _smooth_angle(self, new_angle):
        """Smooth angle to prevent jumps"""
        if self._detect_angle_jump(new_angle):
            # Use predicted angle from Kalman filter instead
            predicted_pos = self.get_predicted_position()
            smoothed_angle = predicted_pos['aizmuth_angle']
            print(f"Angle jump detected: {new_angle:.1f}° -> {smoothed_angle:.1f}°")
        else:
            smoothed_angle = new_angle
            self.last_valid_angle = new_angle
            
        self.angle_history.append(smoothed_angle)
        if len(self.angle_history) > 5:
            self.angle_history.pop(0)
            
        return smoothed_angle

    def update(self, detection):
        """Update target with new detection"""
        # Smooth the angle to prevent jumps
        smoothed_angle = self._smooth_angle(detection['aizmuth_angle'])
        detection['aizmuth_angle'] = smoothed_angle
        
        # Recalculate x,y with smoothed angle
        range_val = detection['range']
        angle_rad = np.radians(smoothed_angle)
        detection['x'] = range_val * np.cos(angle_rad)
        detection['y'] = range_val * np.sin(angle_rad)
        
        # Update Kalman filter
        z = np.array([detection['x'], detection['y']])
        self.kf.predict()
        self.kf.update(z)

        # Update target properties
        self.last_detection = detection
        self.detection_history.append(detection)
        self.last_update_time = time.time()
        self.consecutive_misses = 0

        # Update classification with confidence
        self.classification_history.append(detection['classification'])
        self.classification_counts[detection['classification']] = self.classification_counts.get(detection['classification'], 0) + 1

        # Update most frequent classification (with minimum confidence)
        if len(self.classification_history) >= 3:
            self.classified_as = max(self.classification_counts, key=self.classification_counts.get)
        
        # Track velocity for consistency
        velocity_raw = detection.get('velocity_raw', detection['speed'])
        self.velocity_history.append(velocity_raw)
        if len(self.velocity_history) > 10:
            self.velocity_history.pop(0)

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
        
        # Ensure azimuth is in valid range
        azimuth = max(-MAX_AZIMUTH, min(azimuth, MAX_AZIMUTH))
        
        range_val = np.sqrt(x**2 + y**2)
        
        return {
            'x': x,
            'y': y,
            'speed': speed,
            'aizmuth_angle': azimuth,
            'range': range_val
        }
    
    def get_confidence_score(self):
        """Calculate confidence score based on detection history"""
        if len(self.detection_history) < 2:
            return 0.5
            
        # Factors affecting confidence:
        # 1. Number of detections
        detection_score = min(len(self.detection_history) / 10, 1.0)
        
        # 2. Consistency of signal strength
        signal_strengths = [d['signal_strength'] for d in self.detection_history[-5:]]
        signal_consistency = 1.0 - (np.std(signal_strengths) / np.mean(signal_strengths)) if np.mean(signal_strengths) > 0 else 0.5
        
        # 3. Velocity consistency
        velocity_consistency = 1.0 - (np.std(self.velocity_history[-5:]) / (np.mean(np.abs(self.velocity_history[-5:])) + 0.1))
        
        # 4. Time since last update
        time_factor = max(0, 1.0 - (time.time() - self.last_update_time) / 2.0)
        
        confidence = (detection_score * 0.3 + signal_consistency * 0.3 + velocity_consistency * 0.2 + time_factor * 0.2)
        
        return max(0, min(1, confidence))
    
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
            'last_seen': time.time() - self.last_update_time,
            'confidence': self.get_confidence_score(),
            'consecutive_misses': self.consecutive_misses
        })
        
        return state

class RadarTracker:
    def __init__(self, max_distance=2.0, max_age=3, hit_threshold=2):
        """
        Initialize tracker with more conservative parameters
        
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
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'new_tracks': 0,
            'updated_tracks': 0,
            'removed_tracks': 0
        }
    
    def update(self, detections):
        """Update tracker with new detections"""
        self.stats['total_detections'] += len(detections)
        
        # Predict new locations for all tracks
        for track in self.tracks:
            track.predict()
        
        # Associate detections with existing tracks
        unmatched_detections = self._associate_detections_to_tracks(detections)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            self.tracks.append(RadarTarget(detection))
            self.stats['new_tracks'] += 1
        
        # Remove old tracks
        self._cleanup_tracks()
        
        # Return current tracks
        return self.get_tracks()
    
    def _associate_detections_to_tracks(self, detections):
        """Associate detections with existing tracks using improved nearest neighbor approach"""
        if not self.tracks:
            return detections
        
        if not detections:
            # No detections, increment consecutive misses for all tracks
            for track in self.tracks:
                track.consecutive_misses += 1
            return []
        
        # Calculate distance matrix with multiple metrics
        distance_matrix = np.zeros((len(self.tracks), len(detections)))
        
        for i, track in enumerate(self.tracks):
            predicted = track.get_predicted_position()
            for j, detection in enumerate(detections):
                # Calculate weighted distance considering multiple factors
                
                # 1. Euclidean distance
                pos_dist = np.sqrt((predicted['x'] - detection['x'])**2 + 
                                 (predicted['y'] - detection['y'])**2)
                
                # 2. Velocity difference
                vel_diff = abs(predicted['speed'] - detection['speed'])
                
                # 3. Angle difference (handle wrapping)
                angle_diff = abs(predicted['aizmuth_angle'] - detection['aizmuth_angle'])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # 4. Signal strength consistency
                signal_diff = abs(track.last_detection['signal_strength'] - detection['signal_strength'])
                
                # Weighted combination
                combined_distance = (pos_dist * 1.0 + 
                                   vel_diff * 0.3 + 
                                   angle_diff * 0.1 + 
                                   signal_diff * 0.1)
                
                distance_matrix[i, j] = combined_distance
        
        # Hungarian algorithm would be better, but using greedy for simplicity
        matched_detections = set()
        unmatched_detections = []
        
        # Sort tracks by confidence (update higher confidence tracks first)
        track_indices = list(range(len(self.tracks)))
        track_indices.sort(key=lambda i: self.tracks[i].get_confidence_score(), reverse=True)
        
        # For each track, find nearest detection
        for i in track_indices:
            track = self.tracks[i]
            
            if len(detections) == 0:
                track.consecutive_misses += 1
                continue
                
            # Get detections sorted by distance
            detection_distances = [(j, distance_matrix[i, j]) for j in range(len(detections))]
            detection_distances.sort(key=lambda x: x[1])
            
            # Try to match with closest detection
            matched = False
            for j, dist in detection_distances:
                if j not in matched_detections and dist <= self.max_distance:
                    track.update(detections[j])
                    matched_detections.add(j)
                    self.stats['updated_tracks'] += 1
                    matched = True
                    break
            
            if not matched:
                track.consecutive_misses += 1
        
        # Collect unmatched detections
        for j, detection in enumerate(detections):
            if j not in matched_detections:
                unmatched_detections.append(detection)
        
        return unmatched_detections
    
    def _cleanup_tracks(self):
        """Remove old tracks with improved criteria"""
        current_time = time.time()
        tracks_to_remove = []
        
        for track in self.tracks:
            should_remove = False
            
            # Remove if too old
            if current_time - track.last_update_time > self.max_age:
                should_remove = True
                
            # Remove if too many consecutive misses
            if track.consecutive_misses >= 5:
                should_remove = True
                
            # Remove if confidence is too low for extended period
            if track.get_confidence_score() < 0.2 and len(track.detection_history) > 5:
                should_remove = True
                
            if should_remove:
                tracks_to_remove.append(track)
        
        for track in tracks_to_remove:
            self.tracks.remove(track)
            self.stats['removed_tracks'] += 1
    
    def get_tracks(self):
        """Get list of current tracks with improved filtering"""
        valid_tracks = []
        
        for track in self.tracks:
            # Only return tracks that meet the hit threshold
            if len(track.detection_history) >= self.hit_threshold:
                # Additional quality checks
                confidence = track.get_confidence_score()
                
                # Only return high-confidence tracks or those with enough history
                if confidence > 0.3 or len(track.detection_history) > 5:
                    valid_tracks.append(track.get_state())
        
        return valid_tracks
    
    def get_statistics(self):
        """Get tracker statistics"""
        return {
            **self.stats,
            'active_tracks': len(self.tracks),
            'confirmed_tracks': len(self.get_tracks())
        }

# Function to integrate with your existing code
def process_and_track_targets(targets, tracker):
    """
    Process radar targets and update tracker with improved filtering
    
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
        # Only process targets with sufficient movement or strong signal
        should_include = False
        
        # Include if moving significantly
        if abs(target['speed']) > 0.3:
            should_include = True
            
        # Include if signal is strong enough
        if target['signal_strength'] > SIGNAL_STRENGTH_THRESHOLD:
            should_include = True
            
        # Include if high confidence
        if target.get('confidence', 0) > 0.6:
            should_include = True
            
        # Include if established track
        if target.get('age', 0) > 3:
            should_include = True
        
        if should_include:
            # Calculate additional metrics for valid targets
            if abs(target['speed']) > 0.2:  # If moving
                # Predict position in 2 seconds
                x_future = target['x'] + 2 * target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
                y_future = target['y'] + 2 * target['speed'] * np.sin(np.radians(target['aizmuth_angle']))
                target['predicted_x'] = x_future
                target['predicted_y'] = y_future
                
                # Keep azimuth in valid range
                target['aizmuth_angle'] = max(-MAX_AZIMUTH, min(target['aizmuth_angle'], MAX_AZIMUTH))
                
                # Calculate time to closest approach (TCA)
                if abs(target['speed']) > 0 and target['range'] > 0:
                    # Radial velocity component
                    v_radial = target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
                    if v_radial < 0:  # Target is approaching
                        tca = -target['range'] / v_radial if v_radial != 0 else float('inf')
                        target['time_to_closest_approach'] = round(tca, 2)
                        
                        # Add alert level based on TCA
                        if tca < 10:
                            target['alert_level'] = 'HIGH'
                        elif tca < 30:
                            target['alert_level'] = 'MEDIUM'
                        else:
                            target['alert_level'] = 'LOW'
                    else:
                        target['alert_level'] = 'LOW'
            
            # Add quality metrics
            target['quality'] = 'HIGH' if target.get('confidence', 0) > 0.7 else 'MEDIUM' if target.get('confidence', 0) > 0.4 else 'LOW'
            
            filtered_targets.append(target)
    
    return filtered_targets