# tracker.py

import math
import itertools
from config4 import *

track_id_counter = itertools.count(1)

# RANGE_THRESHOLD = 1.0      # meters
# AZIMUTH_THRESHOLD = 5.0    # degrees
# SIGNAL_STRENGTH_MIN = 0.005

class Track:
    def __init__(self, detection):
        self.track_id = next(track_id_counter)
        self.data = detection.copy()
        self.missed_frames = 0
        self.confidence = 1

    def update(self, detection):
        self.data.update(detection)
        self.missed_frames = 0
        self.confidence += 1

    def get_state(self):
        state = self.data.copy()
        state.update({
            "track_id": self.track_id,
            "confidence": self.confidence,
            "missed_frames": self.missed_frames
        })
        return state

    @property
    def range(self):
        return self.data.get('range', 0)

    @property
    def azimuth(self):
        return self.data.get('azimuth', 0)

    @property
    def signal_strength(self):
        return self.data.get('signal_strength', 0)

def is_match(det, track):
    return (
        abs(det['range'] - track.range) < RANGE_THRESHOLD and
        abs(det['azimuth'] - track.azimuth) < AZIMUTH_THRESHOLD
    )

def update_tracks(detections, tracks):
    # filtered = [d for d in detections if d['signal_strength'] >= SIGNAL_STRENGTH_MIN]
    updated_tracks = []

    for det in detections:
        matched = False
        for track in tracks:
            if is_match(det, track):
                track.update(det)
                matched = True
                updated_tracks.append(track)
                break
        if not matched:
            new_track = Track(det)
            updated_tracks.append(new_track)

    for track in tracks:
        if track not in updated_tracks:
            track.missed_frames += 1
            track.confidence -= 1
            if track.confidence > 0 and track.missed_frames <= MAX_MISSED_FRAMES:
                updated_tracks.append(track)

    return [t for t in updated_tracks if t.confidence > 0 or t.missed_frames <= MAX_MISSED_FRAMES]
