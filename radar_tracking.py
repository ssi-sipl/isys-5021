import numpy as np
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
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
        
        # Tracking quality metrics
        self.confidence_score = 0.5  # Initial confidence
        self.quality_score = 0.0
        self.velocity_consistency = 0.0
        self.position_consistency = 0.0
        
        # Initialize Kalman filter with improved parameters
        self.kf = self._initialize_kalman_filter(target_info)
        
    def _initialize_kalman_filter(self, detection):
        """Initialize Kalman filter with improved 6 state variables (x, y, vx, vy, ax, ay)"""
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
        
        # Adaptive measurement noise based on signal strength
        base_noise = 2.0  # Reduced from 5.0 for better tracking
        signal_strength = detection.get('signal_strength', 50)
        noise_factor = max(0.5, (100 - signal_strength) / 100)  # Lower noise for stronger signals
        
        kf.R = np.array([
            [base_noise * noise_factor, 0],
            [0, base_noise * noise_factor]
        ])
        
        # Improved process noise matrix
        q = 0.01  # Increased from 0.001 for more responsive tracking
        kf.Q = np.array([
            [q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2, 0],
            [0, q/4*dt**4, 0, q/2*dt**3, 0, q/2*dt**2],
            [q/2*dt**3, 0, q*dt**2, 0, q*dt, 0],
            [0, q/2*dt**3, 0, q*dt**2, 0, q*dt],
            [q/2*dt**2, 0, q*dt, 0, q, 0],
            [0, q/2*dt**2, 0, q*dt, 0, q]
        ])
        
        # Initial state with better velocity estimation
        initial_vx = detection['speed'] * np.cos(np.radians(detection['aizmuth_angle']))
        initial_vy = detection['speed'] * np.sin(np.radians(detection['aizmuth_angle']))
        
        kf.x = np.array([
            [detection['x']],
            [detection['y']],
            [initial_vx],
            [initial_vy],
            [0],  # Initial acceleration
            [0]
        ]).reshape(6, 1)
        
        # More conservative initial covariance
        kf.P = np.eye(6) * 10  # Reduced from 50
        
        return kf

    def update(self, detection):
        """Update target with new detection and quality assessment"""
        # Store previous state for consistency checking
        prev_x, prev_y = self.kf.x[0, 0], self.kf.x[1, 0]
        prev_vx, prev_vy = self.kf.x[2, 0], self.kf.x[3, 0]
        
        # Update Kalman filter
        z = np.array([detection['x'], detection['y']])
        self.kf.predict()
        self.kf.update(z)
        
        # Calculate quality metrics
        self._update_quality_metrics(detection, prev_x, prev_y, prev_vx, prev_vy)
        
        # Update target properties
        self.last_detection = detection
        self.detection_history.append(detection)
        self.last_update_time = time.time()
        self.consecutive_misses = 0
        
        # Update classification with weighted voting
        self.classification_history.append(detection['classification'])
        self.classification_counts[detection['classification']] = self.classification_counts.get(detection['classification'], 0) + 1
        
        # Update most frequent classification
        self.classified_as = max(self.classification_counts, key=self.classification_counts.get)
        
        # Update signal strength
        if 'signal_strength' in detection:
            self.last_detection['signal_strength'] = detection['signal_strength']
    
    def _update_quality_metrics(self, detection, prev_x, prev_y, prev_vx, prev_vy):
        """Update tracking quality metrics"""
        # Position consistency (how well prediction matches measurement)
        predicted_x, predicted_y = self.kf.x[0, 0], self.kf.x[1, 0]
        position_error = np.sqrt((predicted_x - detection['x'])**2 + (predicted_y - detection['y'])**2)
        self.position_consistency = max(0, 1 - position_error / 2.0)  # Normalized to 0-1
        
        # Velocity consistency (how stable is the velocity)
        if len(self.detection_history) > 1:
            current_vx, current_vy = self.kf.x[2, 0], self.kf.x[3, 0]
            velocity_change = np.sqrt((current_vx - prev_vx)**2 + (current_vy - prev_vy)**2)
            self.velocity_consistency = max(0, 1 - velocity_change / 5.0)  # Normalized to 0-1
        
        # Overall confidence score
        signal_factor = detection.get('signal_strength', 50) / 100.0
        age_factor = min(1.0, len(self.detection_history) / 10.0)  # Increase confidence with age
        miss_factor = max(0.1, 1 - self.consecutive_misses / 5.0)
        
        self.confidence_score = (
            0.3 * self.position_consistency +
            0.3 * self.velocity_consistency +
            0.2 * signal_factor +
            0.1 * age_factor +
            0.1 * miss_factor
        )
        
        # Quality score for track management
        self.quality_score = self.confidence_score * age_factor
    
    def predict(self):
        """Predict next position without measurement update"""
        self.kf.predict()
        return self.get_predicted_position()
    
    def get_predicted_position(self):
        """Get predicted position with uncertainty"""
        x, y = self.kf.x[0, 0], self.kf.x[1, 0]
        vx, vy = self.kf.x[2, 0], self.kf.x[3, 0]
        speed = np.sqrt(vx**2 + vy**2)
        
        # Calculate azimuth from velocity vector
        azimuth = np.degrees(np.arctan2(vy, vx))
        range_val = np.sqrt(x**2 + y**2)
        
        # Calculate prediction uncertainty
        P_pos = self.kf.P[:2, :2]  # Position covariance
        uncertainty = np.sqrt(np.trace(P_pos))
        
        return {
            'x': x,
            'y': y,
            'speed': speed,
            'aizmuth_angle': azimuth,
            'range': range_val,
            'uncertainty': uncertainty
        }
    
    def is_physically_plausible(self, detection, dt=0.1):
        """Check if detection is physically plausible given current state"""
        if len(self.detection_history) < 2:
            return True
        
        # Check maximum acceleration constraint
        predicted = self.get_predicted_position()
        distance_moved = np.sqrt((detection['x'] - predicted['x'])**2 + 
                               (detection['y'] - predicted['y'])**2)
        
        # Maximum reasonable acceleration for typical radar targets (m/s²)
        max_acceleration = 20.0  # Adjust based on your target types
        max_distance = predicted['speed'] * dt + 0.5 * max_acceleration * dt**2
        
        return distance_moved <= max_distance * 2  # Allow some margin
    
    def get_state(self):
        """Get current state as dict with enhanced tracking info"""
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
            'confidence_score': self.confidence_score,
            'quality_score': self.quality_score,
            'uncertainty': predicted['uncertainty'],
            'consecutive_misses': self.consecutive_misses
        })
        
        return state

class RadarTracker:
    def __init__(self, max_distance=1.0, max_age=3, hit_threshold=3, 
                 min_confidence=0.3, use_hungarian=True):
        """
        Initialize enhanced tracker
        
        Args:
            max_distance: Maximum distance for track association (meters)
            max_age: Maximum time without update before removing track (seconds)
            hit_threshold: Minimum detections before track is considered confirmed
            min_confidence: Minimum confidence score for track validation
            use_hungarian: Use Hungarian algorithm for optimal assignment
        """
        self.tracks = []
        self.max_distance = max_distance
        self.max_age = max_age
        self.hit_threshold = hit_threshold
        self.min_confidence = min_confidence
        self.use_hungarian = use_hungarian
        self.next_id = 1
        
        # Track management parameters
        self.max_tracks = 50  # Limit maximum number of tracks
        self.noise_filter_threshold = 2  # Minimum detections to survive initial filtering
        
    def _prefilter_detections(self, detections):
        """Apply initial filtering to remove obvious false detections"""
        filtered_detections = []
        
        for detection in detections:
            # Signal strength filter
            if detection.get('signal_strength', 0) < 30:  # Adjust threshold as needed
                continue
            
            # Speed filter - remove unrealistic speeds
            if detection.get('speed', 0) > 50:  # 50 m/s = 180 km/h
                continue
            
            # Range filter - remove detections beyond reasonable range
            range_val = detection.get('range', np.sqrt(detection['x']**2 + detection['y']**2))
            if range_val > 100:  # 100 meters max range
                continue
            
            filtered_detections.append(detection)
        
        return filtered_detections
    
    def update(self, detections):
        """Update tracker with new detections using improved association"""
        # Pre-filter detections to remove obvious false positives
        detections = self._prefilter_detections(detections)
        
        # Predict new locations for all tracks
        for track in self.tracks:
            track.predict()
        
        # Associate detections with existing tracks
        if self.use_hungarian and len(self.tracks) > 0 and len(detections) > 0:
            unmatched_detections = self._hungarian_association(detections)
        else:
            unmatched_detections = self._greedy_association(detections)
        
        # Create new tracks for unmatched detections with validation
        for detection in unmatched_detections:
            if len(self.tracks) < self.max_tracks:
                new_track = RadarTarget(detection)
                self.tracks.append(new_track)
        
        # Remove poor quality and old tracks
        self._cleanup_tracks()
        
        # Return current validated tracks
        return self.get_tracks()
    
    def _hungarian_association(self, detections):
        """Use Hungarian algorithm for optimal track-detection assignment"""
        if not self.tracks or not detections:
            return detections
        
        # Create cost matrix
        cost_matrix = np.full((len(self.tracks), len(detections)), np.inf)
        
        for i, track in enumerate(self.tracks):
            predicted = track.get_predicted_position()
            
            for j, detection in enumerate(detections):
                # Calculate Mahalanobis distance for better association
                dx = predicted['x'] - detection['x']
                dy = predicted['y'] - detection['y']
                
                # Use covariance matrix for distance calculation
                P_pos = track.kf.P[:2, :2]
                try:
                    mahal_dist = np.sqrt(np.array([dx, dy]).T @ np.linalg.inv(P_pos) @ np.array([dx, dy]))
                except:
                    # Fallback to Euclidean distance if covariance is singular
                    mahal_dist = np.sqrt(dx**2 + dy**2)
                
                # Physical plausibility check
                if not track.is_physically_plausible(detection):
                    continue
                
                # Gate based on distance and uncertainty
                gate_distance = self.max_distance + predicted.get('uncertainty', 0)
                
                if mahal_dist <= gate_distance:
                    # Add classification consistency bonus
                    class_bonus = 0.2 if detection['classification'] == track.classified_as else 0
                    cost_matrix[i, j] = mahal_dist - class_bonus
        
        # Solve assignment problem
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # Update matched tracks
        matched_detections = set()
        for i, j in zip(row_indices, col_indices):
            if cost_matrix[i, j] < np.inf:
                self.tracks[i].update(detections[j])
                matched_detections.add(j)
            else:
                self.tracks[i].consecutive_misses += 1
        
        # Handle unmatched tracks
        for i, track in enumerate(self.tracks):
            if i not in row_indices:
                track.consecutive_misses += 1
        
        # Return unmatched detections
        return [det for j, det in enumerate(detections) if j not in matched_detections]
    
    def _greedy_association(self, detections):
        """Fallback greedy association method"""
        if not self.tracks:
            return detections
        
        if not detections:
            for track in self.tracks:
                track.consecutive_misses += 1
            return []
        
        # Calculate distance matrix with gating
        valid_associations = []
        
        for i, track in enumerate(self.tracks):
            predicted = track.get_predicted_position()
            
            for j, detection in enumerate(detections):
                dx = predicted['x'] - detection['x']
                dy = predicted['y'] - detection['y']
                dist = np.sqrt(dx**2 + dy**2)
                
                # Apply gating and physical plausibility
                gate_distance = self.max_distance + predicted.get('uncertainty', 0)
                
                if dist <= gate_distance and track.is_physically_plausible(detection):
                    valid_associations.append((i, j, dist))
        
        # Sort by distance and assign greedily
        valid_associations.sort(key=lambda x: x[2])
        
        matched_tracks = set()
        matched_detections = set()
        
        for track_idx, det_idx, dist in valid_associations:
            if track_idx not in matched_tracks and det_idx not in matched_detections:
                self.tracks[track_idx].update(detections[det_idx])
                matched_tracks.add(track_idx)
                matched_detections.add(det_idx)
        
        # Handle unmatched tracks
        for i, track in enumerate(self.tracks):
            if i not in matched_tracks:
                track.consecutive_misses += 1
        
        return [det for j, det in enumerate(detections) if j not in matched_detections]
    
    def _cleanup_tracks(self):
        """Enhanced track cleanup with quality-based filtering"""
        current_time = time.time()
        
        tracks_to_keep = []
        
        for track in self.tracks:
            age = len(track.detection_history)
            time_since_update = current_time - track.last_update_time
            
            # Keep track based on multiple criteria
            keep_track = False
            
            # High-quality mature tracks
            if (age >= self.hit_threshold and 
                track.quality_score >= self.min_confidence and
                time_since_update < self.max_age):
                keep_track = True
            
            # Promising new tracks
            elif (age >= self.noise_filter_threshold and 
                  age < self.hit_threshold and 
                  track.consecutive_misses < 3 and
                  time_since_update < self.max_age / 2):
                keep_track = True
            
            # Very recent tracks (give them a chance)
            elif (age < self.noise_filter_threshold and 
                  track.consecutive_misses == 0 and
                  time_since_update < 0.5):
                keep_track = True
            
            if keep_track:
                tracks_to_keep.append(track)
        
        self.tracks = tracks_to_keep
        
        # Limit total number of tracks
        if len(self.tracks) > self.max_tracks:
            # Sort by quality and keep the best ones
            self.tracks.sort(key=lambda t: t.quality_score, reverse=True)
            self.tracks = self.tracks[:self.max_tracks]
    
    def get_tracks(self):
        """Get list of high-quality confirmed tracks"""
        confirmed_tracks = []
        
        for track in self.tracks:
            state = track.get_state()
            
            # Only return tracks that meet quality criteria
            if (len(track.detection_history) >= self.hit_threshold and
                track.confidence_score >= self.min_confidence and
                track.consecutive_misses < 3):
                confirmed_tracks.append(state)
        
        return confirmed_tracks

def process_and_track_targets(targets, tracker):
    """
    Enhanced target processing with improved filtering and validation
    
    Args:
        targets: List of target dictionaries
        tracker: RadarTracker instance
    
    Returns:
        List of high-quality tracked objects with enhanced metadata
    """
    # Update tracker with new detections
    tracked_targets = tracker.update(targets)
    
    filtered_targets = []
    
    for target in tracked_targets:
        # Enhanced motion analysis
        if abs(target['speed']) > 0.2 and target.get('signal_strength', 0) > 30:
            
            # Predict future positions with uncertainty
            x_future = target['x'] + 2 * target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
            y_future = target['y'] + 2 * target['speed'] * np.sin(np.radians(target['aizmuth_angle']))
            
            target['predicted_x'] = x_future
            target['predicted_y'] = y_future
            
            # Clamp azimuth angle to sensor limits
            target['aizmuth_angle'] = max(-75, min(target['aizmuth_angle'], 75))
            
            # Enhanced TCA calculation with confidence
            if abs(target['speed']) > 0.1 and target['range'] > 0:
                v_radial = target['speed'] * np.cos(np.radians(target['aizmuth_angle']))
                if v_radial < 0:  # Approaching target
                    tca = -target['range'] / v_radial
                    target['time_to_closest_approach'] = round(tca, 2)
                    
                    # Add threat assessment
                    if tca < 10 and target['confidence_score'] > 0.7:
                        target['threat_level'] = 'HIGH'
                    elif tca < 30 and target['confidence_score'] > 0.5:
                        target['threat_level'] = 'MEDIUM'
                    else:
                        target['threat_level'] = 'LOW'
                else:
                    target['threat_level'] = 'LOW'
            
            # Only keep high-confidence targets
            if target['confidence_score'] >= 0.3:
                filtered_targets.append(target)
    
    return filtered_targets