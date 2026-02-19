"""
HandAssist Backend - Main Flask Application
This is the server that receives hand landmark data and provides feedback
"""

import os
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify, redirect, url_for, render_template, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from exercises.open_close import HandOpenCloseDetector
from exercises.pinch import PinchDetector
from exercises.abduction_adduction import AbductionAdductionDetector
from exercises.thumb_opposition import ThumbOppositionDetector
from exercises.finger_lifts import FingerLiftsDetector
from state_manager import StateManager

# Create Flask app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=STATIC_DIR,
    static_url_path='/static'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rehability-dev-secret')
CORS(app)  # Allow frontend to communicate with backend

DB_PATH = os.path.join(BASE_DIR, 'rehability.sqlite3')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize detectors and state manager
open_close_detector = HandOpenCloseDetector()
pinch_detector = PinchDetector()
abduction_adduction_detector = AbductionAdductionDetector()
thumb_opposition_detector = ThumbOppositionDetector()
finger_lifts_detector = FingerLiftsDetector()
state_manager = StateManager()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_type TEXT NOT NULL,
                sets_planned INTEGER,
                reps_planned INTEGER,
                reps_completed INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


class User(UserMixin):
    def __init__(self, user_id, username, password_hash):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        if not row:
            return None
        return User(row['id'], row['username'], row['password_hash'])
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_db()
    try:
        row = conn.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ?',
            (username,),
        ).fetchone()
        if not row:
            return None
        return User(row['id'], row['username'], row['password_hash'])
    finally:
        conn.close()


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api') or request.path in ('/analyze', '/reset'):
        return jsonify({'error': 'unauthorized'}), 401
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('app_home'))

    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        user = get_user_by_username(username)
        if not user or not check_password_hash(user.password_hash, password):
            error = 'Invalid username or password'
        else:
            login_user(user)
            return redirect(url_for('app_home'))

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('app_home'))

    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not username or not password:
            error = 'Username and password are required'
        elif get_user_by_username(username):
            error = 'Username already exists'
        else:
            conn = get_db()
            try:
                conn.execute(
                    'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
                    (
                        username,
                        generate_password_hash(password),
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def app_home():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/me')
@login_required
def api_me():
    return jsonify({'username': current_user.username})


@app.route('/api/progress', methods=['GET', 'POST'])
@login_required
def api_progress():
    if request.method == 'POST':
        data = request.get_json() or {}

        exercise_type = (data.get('exercise_type') or '').strip()
        sets_planned = data.get('sets_planned')
        reps_planned = data.get('reps_planned')
        reps_completed = data.get('reps_completed')
        notes = (data.get('notes') or '').strip()

        if exercise_type not in ('open_close', 'pinch', 'abduction_adduction', 'thumb_opposition', 'finger_lifts'):
            return jsonify({'error': 'invalid_exercise_type'}), 400

        conn = get_db()
        try:
            conn.execute(
                """
                INSERT INTO progress (
                    user_id,
                    exercise_type,
                    sets_planned,
                    reps_planned,
                    reps_completed,
                    notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    current_user.id,
                    exercise_type,
                    sets_planned,
                    reps_planned,
                    reps_completed,
                    notes,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return jsonify({'ok': True})

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, exercise_type, sets_planned, reps_planned, reps_completed, notes, created_at
            FROM progress
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 50
            """,
            (current_user.id,),
        ).fetchall()
    finally:
        conn.close()

    return jsonify(
        [
            {
                'id': row['id'],
                'exercise_type': row['exercise_type'],
                'sets_planned': row['sets_planned'],
                'reps_planned': row['reps_planned'],
                'reps_completed': row['reps_completed'],
                'notes': row['notes'],
                'created_at': row['created_at'],
            }
            for row in rows
        ]
    )

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """
    Main endpoint that receives hand landmarks and returns feedback
    
    Expected JSON input:
    {
        "landmarks": [...],  # Array of 21 landmarks from MediaPipe
        "exercise_type": "open_close", "pinch", or "abduction_adduction"
    }
    
    Returns:
    {
        "state": "OPEN", "CLOSED", "SPREAD", or "TRANSITION",
        "repetitions": number,
        "feedback": "text message for user"
    }
    """
    try:
        # Get data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        landmarks = data.get('landmarks')
        exercise_type = (data.get('exercise_type') or 'open_close').strip()
        
        if not landmarks:
            return jsonify({"error": "No landmarks provided"}), 400
        
        # Choose the right detector based on exercise type
        if exercise_type == 'open_close':
            detector = open_close_detector
        elif exercise_type == 'pinch':
            detector = pinch_detector
        elif exercise_type == 'abduction_adduction':
            detector = abduction_adduction_detector
        elif exercise_type == 'thumb_opposition':
            detector = thumb_opposition_detector
        elif exercise_type == 'finger_lifts':
            detector = finger_lifts_detector
        else:
            return jsonify({"error": f"Unknown exercise type: {exercise_type}"}), 400
        
        # Analyze the landmarks
        if exercise_type == 'thumb_opposition':
            seq = ('INDEX', 'MIDDLE', 'RING', 'PINKY')
            expected = seq[state_manager.states['thumb_opposition'].get('sequence_index', 0)]

            touched = None
            for finger in seq:
                try:
                    if detector.detect_touch_target(landmarks, finger):
                        touched = finger
                        break
                except Exception:
                    touched = None

            if touched == expected:
                current_state = f'TOUCH_{touched}'
                phase = 'TOUCH'
            elif touched is None:
                current_state = 'RELEASE'
                phase = 'RELEASE'
            else:
                current_state = 'TRANSITION'
                phase = 'TRANSITION'

            # Update state manager and get repetition count
            try:
                state_changed, repetitions = state_manager.update_state(
                    exercise_type,
                    current_state,
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            feedback = detector.get_feedback(phase, expected)
        else:
            current_state = detector.detect_state(landmarks)

            # Update state manager and get repetition count
            try:
                state_changed, repetitions = state_manager.update_state(
                    exercise_type,
                    current_state,
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            # Generate feedback message
            feedback = detector.get_feedback(current_state) if hasattr(detector, 'get_feedback') else detector.generate_feedback(current_state, state_changed)
        
        # Return results
        return jsonify({
            "state": current_state,
            "repetitions": repetitions,
            "feedback": feedback,
            "state_changed": state_changed
        })
    
    except Exception as e:
        print(f"Error in /analyze: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    """Reset the exercise state and repetition counter"""
    try:
        data = request.get_json()
        exercise_type = data.get('exercise_type', 'open_close')
        
        state_manager.reset(exercise_type)
        
        return jsonify({
            "message": "State reset successfully",
            "exercise_type": exercise_type
        })
    
    except Exception as e:
        print(f"Error in /reset: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("HandAssist Backend Starting...")
    print("=" * 50)
    print("Server will run on: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run the Flask development server
    init_db()
    app.run(
        debug=True,  # Shows detailed error messages
        host='127.0.0.1',  # Only accessible from your computer
        port=5000  # Port number
    )