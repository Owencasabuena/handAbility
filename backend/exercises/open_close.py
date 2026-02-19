"""
Hand Open/Close Detector
Detects whether a hand is open or closed based on finger positions
"""

import math

class HandOpenCloseDetector:
    """
    Detects hand open/close state by measuring distances between fingertips and wrist
    """
    
    def __init__(self):
        # Thresholds for determining open vs closed hand
        # These are normalized values (0-1) from MediaPipe
        self.OPEN_THRESHOLD = 0.25   # Hand is open if avg distance > this
        self.CLOSED_THRESHOLD = 0.15  # Hand is closed if avg distance < this
        
        # MediaPipe Hand Landmark Indices
        # 0 = Wrist
        # 8 = Index finger tip
        # 12 = Middle finger tip
        # 16 = Ring finger tip
        # 20 = Pinky tip
        self.WRIST = 0
        self.FINGERTIPS = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    
    def calculate_distance(self, point1, point2):
        """
        Calculate Euclidean distance between two 3D points
        
        Args:
            point1: Dictionary with 'x', 'y', 'z' keys
            point2: Dictionary with 'x', 'y', 'z' keys
        
        Returns:
            Float distance
        """
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        dz = point1['z'] - point2['z']
        
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def detect_state(self, landmarks):
        """
        Detect if hand is OPEN, CLOSED, or in TRANSITION
        
        Args:
            landmarks: List of 21 landmark dictionaries from MediaPipe
                      Each has 'x', 'y', 'z' coordinates
        
        Returns:
            String: 'OPEN', 'CLOSED', or 'TRANSITION'
        """
        if not landmarks or len(landmarks) < 21:
            return 'TRANSITION'
        
        try:
            # Get wrist position
            wrist = landmarks[self.WRIST]
            
            # Calculate distances from each fingertip to wrist
            distances = []
            for fingertip_index in self.FINGERTIPS:
                fingertip = landmarks[fingertip_index]
                distance = self.calculate_distance(wrist, fingertip)
                distances.append(distance)
            
            # Calculate average distance
            avg_distance = sum(distances) / len(distances)
            
            # Determine state based on average distance
            if avg_distance > self.OPEN_THRESHOLD:
                return 'OPEN'
            elif avg_distance < self.CLOSED_THRESHOLD:
                return 'CLOSED'
            else:
                return 'TRANSITION'
        
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error detecting state: {e}")
            return 'TRANSITION'
    
    def generate_feedback(self, state, state_changed):
        """
        Generate user-friendly feedback message in Tagalog
        
        Args:
            state: Current state ('OPEN', 'CLOSED', 'TRANSITION')
            state_changed: Boolean indicating if state just changed
        
        Returns:
            String feedback message in Tagalog
        """
        if not state_changed:
            return ""  # No new feedback if state didn't change
        
        feedback_messages = {
            'OPEN': 'Magaling! Bukas na ang kamay',
            'CLOSED': 'Magaling! Sarado na ang kamay',
            'TRANSITION': 'Ipagpatuloy...'
        }
        
        return feedback_messages.get(state, '')