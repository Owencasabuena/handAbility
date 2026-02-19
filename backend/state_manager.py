"""
State Manager - Tracks exercise state and counts repetitions
Uses a Finite State Machine (FSM) to ensure accurate counting
"""

import time

class StateManager:
    """
    Manages the state transitions for exercises
    Implements a Finite State Machine: OPEN → CLOSED → OPEN = 1 repetition
    """
    
    def __init__(self):
        # Store state for each exercise type
        self.states = {
            'open_close': {
                'current_state': 'OPEN',
                'previous_state': 'OPEN',
                'repetitions': 0,
                'last_state_change': time.time()
            },
            'pinch': {
                'current_state': 'OPEN',
                'previous_state': 'OPEN',
                'repetitions': 0,
                'last_state_change': time.time()
            },
            'abduction_adduction': {
                'current_state': 'CLOSED',
                'previous_state': 'CLOSED',
                'repetitions': 0,
                'last_state_change': time.time()
            },
            'thumb_opposition': {
                'current_state': 'TRACKING',
                'previous_state': 'TRACKING',
                'repetitions': 0,
                'last_state_change': time.time(),
                'sequence_index': 0,
                'is_touching': False,
            },
            'finger_lifts': {
                'current_state': 'NONE',
                'previous_state': 'NONE',
                'repetitions': 0,
                'last_state_change': time.time(),
            }
        }
        
        # Minimum time (in seconds) a state must be held before changing
        # This prevents accidental quick movements from being counted
        self.MIN_STATE_DURATION = 0.2  # 200 milliseconds
    
    def update_state(self, exercise_type, new_state):
        """
        Update the current state and count repetitions if needed
        
        Args:
            exercise_type: 'open_close' or 'pinch'
            new_state: 'OPEN', 'CLOSED', or 'TRANSITION'
        
        Returns:
            (state_changed, repetitions): Tuple of whether state changed and current rep count
        """
        if exercise_type not in self.states:
            raise ValueError(f"Unknown exercise type: {exercise_type}")
        
        exercise_state = self.states[exercise_type]
        current_state = exercise_state['current_state']

        # Special handling for thumb opposition progression
        if exercise_type == 'thumb_opposition':
            # new_state expected to be one of: TOUCH_<FINGER>, RELEASE, TRANSITION
            if new_state.startswith('TOUCH_'):
                finger = new_state.replace('TOUCH_', '')
                expected = ('INDEX', 'MIDDLE', 'RING', 'PINKY')[exercise_state.get('sequence_index', 0)]
                if finger == expected and not exercise_state.get('is_touching', False):
                    exercise_state['is_touching'] = True
                    exercise_state['sequence_index'] = (exercise_state.get('sequence_index', 0) + 1) % 4
                    # Count rep when we advance past PINKY (i.e. index wraps to 0)
                    if exercise_state['sequence_index'] == 0:
                        exercise_state['repetitions'] += 1
                        print(f"✓ Repetition counted! Total: {exercise_state['repetitions']}")
                    exercise_state['previous_state'] = current_state
                    exercise_state['current_state'] = new_state
                    exercise_state['last_state_change'] = time.time()
                    return True, exercise_state['repetitions']
                return False, exercise_state['repetitions']

            if new_state in ('RELEASE', 'TRANSITION'):
                # allow next touch only after release
                if exercise_state.get('is_touching', False):
                    exercise_state['is_touching'] = False
                    exercise_state['previous_state'] = current_state
                    exercise_state['current_state'] = new_state
                    exercise_state['last_state_change'] = time.time()
                    return True, exercise_state['repetitions']
                return False, exercise_state['repetitions']

            return False, exercise_state['repetitions']

        # Special handling for finger lifts
        if exercise_type == 'finger_lifts':
            # Normalize transitional states
            if new_state == 'TRANSITIONING':
                new_state = 'TRANSITION'
            if new_state == 'TRANSITION':
                return False, exercise_state['repetitions']

            # Count a repetition when a finger that was up returns to NONE
            if current_state.endswith('_UP') and new_state == 'NONE':
                exercise_state['repetitions'] += 1
                print(f"✓ Repetition counted! Total: {exercise_state['repetitions']}")

            if new_state != current_state:
                exercise_state['previous_state'] = current_state
                exercise_state['current_state'] = new_state
                exercise_state['last_state_change'] = time.time()
                return True, exercise_state['repetitions']

            return False, exercise_state['repetitions']
        
        # Check if enough time has passed since last state change
        time_since_change = time.time() - exercise_state['last_state_change']
        
        # Normalize transitional states
        if new_state == 'TRANSITIONING':
            new_state = 'TRANSITION'

        # Ignore TRANSITION states - they're just in-between positions
        if new_state == 'TRANSITION':
            return False, exercise_state['repetitions']
        
        # Only change state if enough time has passed (prevents noise)
        if new_state != current_state and time_since_change >= self.MIN_STATE_DURATION:
            # Counting logic depends on exercise type
            if exercise_type in ('open_close', 'pinch'):
                # Check if we completed a full cycle: OPEN → CLOSED → OPEN
                if current_state == 'CLOSED' and new_state == 'OPEN':
                    exercise_state['repetitions'] += 1
                    print(f"✓ Repetition counted! Total: {exercise_state['repetitions']}")
            elif exercise_type == 'abduction_adduction':
                # Check if we completed a full cycle: SPREAD → CLOSED → SPREAD
                if current_state == 'CLOSED' and new_state == 'SPREAD':
                    exercise_state['repetitions'] += 1
                    print(f"✓ Repetition counted! Total: {exercise_state['repetitions']}")
            
            # Update state
            exercise_state['previous_state'] = current_state
            exercise_state['current_state'] = new_state
            exercise_state['last_state_change'] = time.time()
            
            return True, exercise_state['repetitions']
        
        # No state change
        return False, exercise_state['repetitions']
    
    def reset(self, exercise_type):
        """Reset state and repetitions for an exercise"""
        if exercise_type in self.states:
            self.states[exercise_type] = {
                'current_state': 'OPEN',
                'previous_state': 'OPEN',
                'repetitions': 0,
                'last_state_change': time.time()
            }
            print(f"State reset for {exercise_type}")
    
    def get_current_state(self, exercise_type):
        """Get the current state for an exercise"""
        if exercise_type in self.states:
            return self.states[exercise_type]['current_state']
        return 'OPEN'
    
    def get_repetitions(self, exercise_type):
        """Get the repetition count for an exercise"""
        if exercise_type in self.states:
            return self.states[exercise_type]['repetitions']
        return 0