import math
from typing import List, Dict, Any, Optional

class AbductionAdductionDetector:
    """
    Detects abduction (spreading fingers) and adduction (bringing fingers together) 
    using finger distance measurements from MediaPipe hand landmarks.
    """
    
    def __init__(self):
        self.finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        self.finger_mcp = [2, 5, 9, 13, 17]  # Metacarpophalangeal joints
        # Thresholds are based on distances normalized by palm size.
        # Tune these in small increments (0.01) if needed.
        self.spread_threshold = 0.34  # Wider gaps between adjacent fingers
        self.closed_threshold = 0.20  # Fingers close together

    def _dist(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        return math.sqrt((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2)

    def _palm_size(self, landmarks: List[Dict[str, Any]]) -> float:
        # Use wrist (0) to middle MCP (9) as a stable palm-size reference.
        if len(landmarks) < 10:
            return 1.0
        size = self._dist(landmarks[0], landmarks[9])
        return max(size, 1e-6)
        
    def calculate_finger_spread(self, landmarks: List[Dict[str, Any]]) -> float:
        """
        Calculate the average spread between all fingers.
        Returns the average distance between adjacent finger tips.
        """
        if len(landmarks) < 21:
            return 0.0
            
        # Adjacent fingertip gaps (ignore thumb; it's often out-of-plane).
        # Index (8) - Middle (12) - Ring (16) - Pinky (20)
        palm = self._palm_size(landmarks)
        gaps = [
            self._dist(landmarks[8], landmarks[12]) / palm,
            self._dist(landmarks[12], landmarks[16]) / palm,
            self._dist(landmarks[16], landmarks[20]) / palm,
        ]
        return sum(gaps) / len(gaps)
    
    def calculate_finger_proximity(self, landmarks: List[Dict[str, Any]]) -> float:
        """
        Calculate how close fingers are to each other.
        Returns the average distance between all finger tips.
        """
        if len(landmarks) < 21:
            return 0.0
            
        # Use the same adjacent fingertip gaps as a proximity signal.
        palm = self._palm_size(landmarks)
        gaps = [
            self._dist(landmarks[8], landmarks[12]) / palm,
            self._dist(landmarks[12], landmarks[16]) / palm,
            self._dist(landmarks[16], landmarks[20]) / palm,
        ]
        return sum(gaps) / len(gaps)
    
    def detect_state(self, landmarks: List[Dict[str, Any]]) -> str:
        """
        Detect if hand is in abduction (spread) or adduction (closed) state.
        """
        if not landmarks or len(landmarks) < 21:
            return "UNKNOWN"
            
        gap = self.calculate_finger_spread(landmarks)

        # Determine state based on normalized adjacent fingertip gaps.
        # Use a small deadband to reduce flicker.
        if gap >= self.spread_threshold:
            return "SPREAD"
        if gap <= self.closed_threshold:
            return "CLOSED"
        return "TRANSITIONING"
    
    def get_feedback(self, state: str) -> str:
        """
        Get Tagalog feedback based on detected state.
        """
        feedback_map = {
            "SPREAD": "Maganda! Ikalat ang mga daliri mo.",
            "CLOSED": "Maayos! Magkabig na ang mga daliri.",
            "TRANSITIONING": "Konti na lang!",
            "UNKNOWN": "Hindi mahanap ang kamay."
        }
        return feedback_map.get(state, "Hindi mahanap ang kamay.")
