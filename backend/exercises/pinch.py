"""
Pinch Detector
Detects pinch gesture by measuring distance between thumb and index finger
"""

import math

class PinchDetector:
    """
    Detects pinch gesture (thumb touching index finger)
    """
    
    def __init__(self):
        # Thresholds for determining pinch state
        # These are normalized values (0-1) from MediaPipe
        self.OPEN_THRESHOLD = 0.08   # Fingers apart if distance > this
        self.CLOSED_THRESHOLD = 0.04  # Pinching if distance < this
        
        # MediaPipe Hand Landmark Indices
        # 4 = Thumb tip
        # 8 = Index finger tip
        self.THUMB_TIP = 4
        self.INDEX_TIP = 8
    
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
        Detect if fingers are OPEN (apart), CLOSED (pinching), or in TRANSITION
        
        Args:
            landmarks: List of 21 landmark dictionaries from MediaPipe
                      Each has 'x', 'y', 'z' coordinates
        
        Returns:
            String: 'OPEN', 'CLOSED', or 'TRANSITION'
        """
        if not landmarks or len(landmarks) < 21:
            return 'TRANSITION'
        
        try:
            # Get thumb and index finger tip positions
            thumb = landmarks[self.THUMB_TIP]
            index = landmarks[self.INDEX_TIP]
            
            # Calculate distance between thumb and index finger
            distance = self.calculate_distance(thumb, index)
            
            # Determine state based on distance
            if distance > self.OPEN_THRESHOLD:
                return 'OPEN'
            elif distance < self.CLOSED_THRESHOLD:
                return 'CLOSED'
            else:
                return 'TRANSITION'
        
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error detecting pinch state: {e}")
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
            'OPEN': 'Magaling! Hiwalay ang mga daliri',
            'CLOSED': 'Perpekto ang pagkapit!',
            'TRANSITION': 'Ipagpatuloy...'
        }
        
        return feedback_messages.get(state, '')