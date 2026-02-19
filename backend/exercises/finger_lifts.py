import math
from typing import Any, Dict, List


class FingerLiftsDetector:
    """Detect individual finger flexion-extension (finger lifts).

    Heuristic:
    - Determine the most "raised" finger by comparing tip y to its PIP y.
      (In MediaPipe normalized coords, smaller y is higher on the screen.)

    State:
    - Returns one of: 'INDEX_UP', 'MIDDLE_UP', 'RING_UP', 'PINKY_UP', 'NONE', 'TRANSITION'

    Rep definition (handled by StateManager):
    - Count 1 repetition when user lifts ANY finger up and then returns to NONE.
    """

    def __init__(self):
        # tips and pips for index/middle/ring/pinky
        self.fingers = {
            'INDEX': (8, 6),
            'MIDDLE': (12, 10),
            'RING': (16, 14),
            'PINKY': (20, 18),
        }
        self.up_threshold = 0.055  # normalized by palm size (approx)
        self.down_threshold = 0.035

    def _dist(self, a: Dict[str, Any], b: Dict[str, Any]) -> float:
        return math.sqrt((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2)

    def _palm_size(self, landmarks: List[Dict[str, Any]]) -> float:
        if len(landmarks) < 10:
            return 1.0
        size = self._dist(landmarks[0], landmarks[9])
        return max(size, 1e-6)

    def detect_state(self, landmarks: List[Dict[str, Any]]) -> str:
        if not landmarks or len(landmarks) < 21:
            return 'UNKNOWN'

        palm = self._palm_size(landmarks)

        best_finger = None
        best_score = 0.0
        for name, (tip_idx, pip_idx) in self.fingers.items():
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            # higher finger => pip_y - tip_y positive and large
            score = (pip['y'] - tip['y']) / palm
            if score > best_score:
                best_score = score
                best_finger = name

        # Decide based on thresholds
        if best_finger and best_score >= self.up_threshold:
            return f'{best_finger}_UP'

        if best_score <= self.down_threshold:
            return 'NONE'

        return 'TRANSITION'

    def get_feedback(self, state: str) -> str:
        if state.endswith('_UP'):
            finger = state.replace('_UP', '').lower()
            return f"Good! Lift the {finger} finger."
        if state == 'NONE':
            return 'Keep your hand flat, then lift one finger.'
        if state == 'TRANSITION':
            return 'Slow and steady.'
        return 'Hand not detected.'
