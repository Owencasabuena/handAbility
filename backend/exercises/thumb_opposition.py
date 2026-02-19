import math
from typing import Any, Dict, List


class ThumbOppositionDetector:
    """Detects thumb opposition progression.

    Repetition definition:
    - A rep is counted when the thumb touches a fingertip (INDEX -> MIDDLE -> RING -> PINKY)
      in order. When PINKY touch is completed, the sequence resets.

    Output states:
    - "TOUCHING": thumb is touching the expected finger
    - "RELEASED": thumb is not touching the expected finger
    - "TRANSITION": in-between / unsure
    """

    def __init__(self):
        self.thumb_tip = 4
        self.finger_tips = {
            'INDEX': 8,
            'MIDDLE': 12,
            'RING': 16,
            'PINKY': 20,
        }
        self.sequence = ['INDEX', 'MIDDLE', 'RING', 'PINKY']
        self.touch_threshold = 0.22  # normalized by palm size
        self.release_threshold = 0.28  # hysteresis

    def _dist(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        return math.sqrt((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2)

    def _palm_size(self, landmarks: List[Dict[str, Any]]) -> float:
        if len(landmarks) < 10:
            return 1.0
        size = self._dist(landmarks[0], landmarks[9])
        return max(size, 1e-6)

    def detect_state(self, landmarks: List[Dict[str, Any]]) -> str:
        # state manager will handle counting; here we only provide TOUCHING/RELEASED.
        if not landmarks or len(landmarks) < 21:
            return 'UNKNOWN'
        return 'TRACKING'

    def detect_touch_target(self, landmarks: List[Dict[str, Any]], target_finger: str) -> bool:
        palm = self._palm_size(landmarks)
        thumb = landmarks[self.thumb_tip]
        tip = landmarks[self.finger_tips[target_finger]]
        d = self._dist(thumb, tip) / palm
        return d <= self.touch_threshold

    def detect_released(self, landmarks: List[Dict[str, Any]], target_finger: str) -> bool:
        palm = self._palm_size(landmarks)
        thumb = landmarks[self.thumb_tip]
        tip = landmarks[self.finger_tips[target_finger]]
        d = self._dist(thumb, tip) / palm
        return d >= self.release_threshold

    def get_feedback(self, phase: str, target_finger: str) -> str:
        if phase == 'TOUCH':
            return f"Good! Thumb to {target_finger.lower()} finger."
        if phase == 'RELEASE':
            return "Release, then go to the next finger."
        return "Move slowly and touch each finger in order."
