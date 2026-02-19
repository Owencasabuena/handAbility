/**
 * HandAssist - Main JavaScript Application
 * Handles camera, MediaPipe hand tracking, and communication with Flask backend
 */

// Configuration
const BACKEND_URL = '';
const SEND_INTERVAL = 200; // Send landmarks to backend every 200ms

const EXERCISE_COPY = {
    open_close: {
        title: 'Open–Close Hand',
        subtitle: 'Open your hand fully, then close into a fist.',
        steps: [
            'Click “Start Camera” and allow camera access when prompted',
            'Position your hand in front of the camera (palm facing camera)',
            'Open your hand fully, then close gently into a fist',
            'Move slowly and deliberately for accurate counting'
        ],
        images: [
            { img: '/static/images/open_close_icon.gif', title: 'Open-Close Demo', desc: 'Watch the hand open and close animation.' }
        ]
    },
    pinch: {
        title: 'Index–Thumb Pinch',
        subtitle: 'Touch your thumb to your index finger, then separate.',
        steps: [
            'Click “Start Camera” and allow camera access when prompted',
            'Position your hand in front of the camera (palm facing camera)',
            'Touch thumb tip to index finger tip, then separate',
            'Keep movements slow and controlled'
        ],
        images: [
            { img: '/static/images/pinch_icon.gif', title: 'Pinch Demo', desc: 'Watch the thumb-index pinch animation.' }
        ]
    },
    abduction_adduction: {
        title: 'Abduction & Adduction',
        subtitle: 'Spread your fingers wide, then bring them back together touching.',
        steps: [
            'Click "Start Camera" and allow camera access when prompted',
            'Position your hand in front of the camera (palm facing camera)',
            'Spread your fingers as wide as possible (abduction)',
            'Bring fingers back together until they touch (adduction)',
            'Move slowly and deliberately for accurate counting'
        ],
        images: [
            { img: '/static/images/abduction_adduction_icon.gif', title: 'Abduction & Adduction Demo', desc: 'Watch fingers spread and close animation.' }
        ]
    },
    thumb_opposition: {
        title: 'Thumb Opposition Progression',
        subtitle: 'Touch the tip of your thumb to each fingertip in sequence.',
        steps: [
            'Click "Start Camera" and allow camera access when prompted',
            'Position your hand in front of the camera (palm facing camera)',
            'Touch thumb tip to index fingertip, then separate',
            'Repeat with middle, ring, and pinky fingertips in order',
            'Move slowly and deliberately for accurate counting'
        ],
        images: [
            { img: '/static/images/thumb_opposition_icon.gif', title: 'Thumb Opposition Demo', desc: 'Placeholder animation for thumb-to-finger touches.' }
        ]
    },
    finger_lifts: {
        title: 'Individual Finger Flexion–Extension',
        subtitle: 'Lift one finger at a time while keeping the others flat.',
        steps: [
            'Click "Start Camera" and allow camera access when prompted',
            'Place your hand flat and steady (palm facing camera)',
            'Lift one finger up (extension) while keeping the others still',
            'Lower it back down (flexion), then move to the next finger',
            'Move slowly and deliberately for accurate counting'
        ],
        images: [
            { img: '/static/images/finger_lifts_icon.gif', title: 'Finger Lifts Demo', desc: 'Placeholder animation for individual finger lifts.' }
        ]
    }
};

const MOTIVATION_PHRASES = [
    'Kaya mo yan!',
    'Galingan mo!',
    'Sige pa, kaya yan!',
    'Konti na lang!',
    'Ang galing!',
    'Tuluy-tuloy lang!' 
];

// Global variables
let camera = null;
let hands = null;
let isRunning = false;
let lastSendTime = 0;
let currentExercise = 'open_close';
let audioEnabled = true;

let plannedSets = 3;
let plannedReps = 10;
let currentSet = 1;
let selectedExercise = null;
let isSetPaused = false;
let motivationLevel = 0;
let didAutoOpenSaveModal = false;

// DOM Elements
const videoElement = document.getElementById('video');
const canvasElement = document.getElementById('canvas');
const canvasCtx = canvasElement.getContext('2d');
const startBtn = document.getElementById('start-btn');
const resetBtn = document.getElementById('reset-btn');
const exerciseSelect = document.getElementById('exercise-select');
const audioToggle = document.getElementById('audio-toggle');
const repCountDisplay = document.getElementById('rep-count');
const currentStateDisplay = document.getElementById('current-state');
const feedbackBox = document.getElementById('feedback');

// New RehAbility elements
const userDisplay = document.getElementById('user-display');
const views = document.querySelectorAll('.view');
const viewHome = document.getElementById('view-home');
const viewSetup = document.getElementById('view-setup');
const viewExercise = document.getElementById('view-exercise');
const viewProgress = document.getElementById('view-progress');
const exerciseCards = document.querySelectorAll('.exercise-card');
const goProgressBtn = document.getElementById('go-progress');
const goProgressInlineBtn = document.getElementById('go-progress-inline');
const setupBackBtn = document.getElementById('setup-back');
const exerciseBackBtn = document.getElementById('exercise-back');
const progressBackBtn = document.getElementById('progress-back');
const setupForm = document.getElementById('setup-form');
const setsInput = document.getElementById('sets-input');
const repsInput = document.getElementById('reps-input');
const beginBtn = document.getElementById('begin-btn');
const setupTitle = document.getElementById('setup-title');
const setupSubtitle = document.getElementById('setup-subtitle');
const setupPreview = document.getElementById('setup-preview');
const exerciseTitle = document.getElementById('exercise-title');
const exerciseSubtitle = document.getElementById('exercise-subtitle');
const setCountDisplay = document.getElementById('set-count');
const repTargetDisplay = document.getElementById('rep-target');
const repCountInlineDisplay = document.getElementById('rep-count-inline');
const motivationDisplay = document.getElementById('motivation');
const saveProgressBtn = document.getElementById('save-progress-btn');
const nextSetBtn = document.getElementById('next-set-btn');
const progressModal = document.getElementById('progress-modal');
const modalBackdrop = document.getElementById('modal-backdrop');
const progressForm = document.getElementById('progress-form');
const modalCancelBtn = document.getElementById('modal-cancel');
const modalSetsPlanned = document.getElementById('modal-sets-planned');
const modalRepsPlanned = document.getElementById('modal-reps-planned');
const modalRepsCompleted = document.getElementById('modal-reps-completed');
const modalNotes = document.getElementById('modal-notes');
const progressSummary = document.getElementById('progress-summary');
const progressList = document.getElementById('progress-list');
const instructionsSection = document.getElementById('exercise-instructions');
const instructionsTitle = document.getElementById('instructions-title');
const instructionsSteps = document.getElementById('instructions-steps');
const instructionsTips = document.getElementById('instructions-tips');
const instructionsImages = document.getElementById('instructions-images');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('HandAssist loaded');
    setupEventListeners();
    initializeApp();
});

/**
 * Initialize app: fetch user and show home view
 */
async function initializeApp() {
    try {
        const res = await fetch(`${BACKEND_URL}/api/me`);
        if (res.ok) {
            const { username } = await res.json();
            if (userDisplay) userDisplay.textContent = username;
        }
    } catch (e) {
        console.warn('Failed to fetch user:', e);
    }
    showHomeView();
}

/**
 * View navigation helpers
 */
function showView(targetView) {
    views.forEach(v => v.classList.remove('is-active'));
    targetView.classList.add('is-active');
}
function showHomeView() { showView(viewHome); }
function showSetupView() {
    if (!selectedExercise) return;
    const copy = EXERCISE_COPY[selectedExercise];
    setupTitle.textContent = copy.title;
    setupSubtitle.textContent = copy.subtitle;
    
    // Force GIF animation restart with cache-busting
    const gifSrc = copy.images[0].img;
    const timestamp = Date.now();
    setupPreview.innerHTML = `<img src="${gifSrc}?v=${timestamp}" alt="${copy.images[0].title}" class="setup-preview-gif" width="160" height="160">`;
    
    showView(viewSetup);
}
function showExerciseView() {
    if (!selectedExercise) return;
    const copy = EXERCISE_COPY[selectedExercise];
    exerciseTitle.textContent = copy.title;
    exerciseSubtitle.textContent = copy.subtitle;
    setCountDisplay.textContent = `${currentSet} / ${plannedSets}`;
    repTargetDisplay.textContent = plannedReps;
    repCountInlineDisplay.textContent = '0';
    renderInstructions();
    showView(viewExercise);
}
function showProgressView() {
    renderProgress();
    showView(viewProgress);
}

/**
 * Handle setup form submission: start exercise session
 */
function onSetupSubmit(e) {
    e.preventDefault();
    plannedSets = parseInt(setsInput.value);
    plannedReps = parseInt(repsInput.value);
    currentSet = 1;
    currentExercise = selectedExercise;
    didAutoOpenSaveModal = false;
    showExerciseView();
}

/**
 * Modal helpers
 */
function openProgressModal() {
    if (!modalSetsPlanned || !modalRepsPlanned || !modalRepsCompleted) return;
    modalSetsPlanned.value = plannedSets;
    modalRepsPlanned.value = plannedReps;
    modalRepsCompleted.value = parseInt(repCountDisplay.textContent) || 0;
    modalNotes.value = '';
    progressModal?.classList.add('is-open');
}
function closeProgressModal() {
    progressModal?.classList.remove('is-open');
}

/**
 * Save progress via POST /api/progress
 */
async function onProgressSubmit(e) {
    e.preventDefault();
    const payload = {
        exercise_type: selectedExercise,
        sets_planned: parseInt(modalSetsPlanned.value),
        reps_planned: parseInt(modalRepsPlanned.value),
        reps_completed: parseInt(modalRepsCompleted.value),
        notes: modalNotes.value.trim()
    };
    try {
        const res = await fetch(`${BACKEND_URL}/api/progress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeProgressModal();
            showFeedback('Progress saved!', 'success');
        } else {
            showFeedback('Failed to save progress.', 'error');
        }
    } catch (e) {
        console.error('Save progress error:', e);
        showFeedback('Error saving progress.', 'error');
    }
}

/**
 * Render progress list from GET /api/progress
 */
async function renderProgress() {
    if (!progressSummary || !progressList) return;
    try {
        const items = await fetch(`${BACKEND_URL}/api/progress`).then(r => r.json());
        progressSummary.innerHTML = `<p>${items.length} saved session${items.length === 1 ? '' : 's'}</p>`;
        if (items.length === 0) {
            progressList.innerHTML = '<p>No sessions saved yet.</p>';
            return;
        }
        progressList.innerHTML = items.map(item => `
            <div class="progress-item">
                <div class="progress-header">
                    <strong>${EXERCISE_COPY[item.exercise_type]?.title || item.exercise_type}</strong>
                    <span class="progress-date">${new Date(item.created_at).toLocaleDateString()}</span>
                </div>
                <div class="progress-metrics">
                    <span>${item.sets_planned} sets planned</span> •
                    <span>${item.reps_planned} reps planned</span> •
                    <span>${item.reps_completed} reps completed</span>
                </div>
                ${item.notes ? `<div class="progress-notes">${item.notes}</div>` : ''}
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load progress:', e);
        progressSummary.innerHTML = '<p>Could not load progress.</p>';
        progressList.innerHTML = '';
    }
}

/**
 * Render exercise instructions and images
 */
function renderInstructions() {
    if (!selectedExercise || !instructionsTitle || !instructionsSteps || !instructionsImages) return;
    const copy = EXERCISE_COPY[selectedExercise];
    instructionsTitle.textContent = copy.title;
    instructionsSteps.innerHTML = copy.steps.map(s => `<li>${s}</li>`).join('');
    instructionsImages.innerHTML = copy.images.map(img => `
        <div class="instruction-image">
            <img src="${img.img}" alt="${img.title}" class="instruction-image-gif" width="180" height="180">
            <div class="instruction-image-title">${img.title}</div>
            <div class="instruction-image-desc">${img.desc}</div>
        </div>
    `).join('');
    instructionsSection.style.display = 'block';
}
function setupEventListeners() {
    startBtn.addEventListener('click', toggleCamera);
    resetBtn.addEventListener('click', resetExercise);
    exerciseSelect.addEventListener('change', onExerciseChange);
    audioToggle.addEventListener('change', onAudioToggle);

    // RehAbility navigation
    exerciseCards.forEach(card => {
        card.addEventListener('click', () => {
            selectedExercise = card.dataset.exercise;
            showSetupView();
        });
    });
    goProgressBtn?.addEventListener('click', showProgressView);
    goProgressInlineBtn?.addEventListener('click', showProgressView);
    setupBackBtn?.addEventListener('click', showHomeView);
    exerciseBackBtn?.addEventListener('click', () => {
        stopCamera();
        showSetupView();
    });
    progressBackBtn?.addEventListener('click', () => {
        if (selectedExercise) showSetupView(); else showHomeView();
    });
    setupForm?.addEventListener('submit', onSetupSubmit);
    saveProgressBtn?.addEventListener('click', openProgressModal);
    nextSetBtn?.addEventListener('click', startNextSet);
    modalCancelBtn?.addEventListener('click', closeProgressModal);
    modalBackdrop?.addEventListener('click', closeProgressModal);
    progressForm?.addEventListener('submit', onProgressSubmit);
}

/**
 * Toggle camera on/off
 */
async function toggleCamera() {
    if (isRunning) {
        stopCamera();
    } else {
        await startCamera();
    }
}

/**
 * Start the camera and MediaPipe hands detection
 */
async function startCamera() {
    try {
        showFeedback('Starting camera...', 'info');
        startBtn.disabled = true;
        
        // Initialize MediaPipe Hands
        hands = new Hands({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
            }
        });
        
        // Configure MediaPipe Hands
        hands.setOptions({
            maxNumHands: 1,  // Track only one hand
            modelComplexity: 1,  // 0=lite, 1=full (recommended)
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        
        // Set up the callback for when hands are detected
        hands.onResults(onHandsDetected);
        
        // Set up camera
        camera = new Camera(videoElement, {
            onFrame: async () => {
                await hands.send({image: videoElement});
            },
            width: 640,
            height: 480
        });
        
        // Start camera
        await camera.start();
        
        isRunning = true;
        startBtn.textContent = 'Stop Camera';
        startBtn.disabled = false;
        showFeedback('Camera started! Show your hand...', 'success');
        
    } catch (error) {
        console.error('Error starting camera:', error);
        showFeedback('Error: Could not access camera. Please check permissions.', 'error');
        startBtn.disabled = false;
    }
}

/**
 * Stop the camera
 */
function stopCamera() {
    if (camera) {
        camera.stop();
        camera = null;
    }
    
    if (hands) {
        hands.close();
        hands = null;
    }
    
    isRunning = false;
    startBtn.textContent = 'Start Camera';
    
    // Clear canvas
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    showFeedback('Camera stopped', 'info');
}

/**
 * Called when MediaPipe detects hands in the video
 */
function onHandsDetected(results) {
    // Set canvas size to match video
    canvasElement.width = results.image.width;
    canvasElement.height = results.image.height;
    
    // Clear canvas
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Draw the video frame
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
    
    // If hand detected, draw landmarks and process
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];
        
        // Draw hand landmarks
        drawHandLandmarks(landmarks);
        
        // Send to backend for analysis (throttled)
        const currentTime = Date.now();
        if (currentTime - lastSendTime > SEND_INTERVAL) {
            sendLandmarksToBackend(landmarks);
            lastSendTime = currentTime;
        }
    } else {
        showFeedback('No hand detected. Show your hand to the camera.', 'info');
        currentStateDisplay.textContent = 'No Hand';
    }
    
    canvasCtx.restore();
}

/**
 * Draw hand landmarks and connections on canvas
 */
function drawHandLandmarks(landmarks) {
    // Draw connections (lines between landmarks)
    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
        color: '#00FF00',
        lineWidth: 2
    });
    
    // Draw landmarks (points)
    drawLandmarks(canvasCtx, landmarks, {
        color: '#FF0000',
        lineWidth: 1,
        radius: 3
    });
}

/**
 * Send landmarks to Flask backend for analysis
 */
async function sendLandmarksToBackend(landmarks) {
    try {
        console.log('Sending exercise_type:', currentExercise);
        console.log('Sending landmarks:', landmarks);
        
        const response = await fetch(`${BACKEND_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                landmarks: landmarks,
                exercise_type: currentExercise
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update UI with results
        updateUI(data);
        
    } catch (error) {
        console.error('Error sending to backend:', error);
        showFeedback('Backend connection error. Make sure Flask server is running!', 'error');
    }
}

/**
 * Start next set: reset counters and update UI
 */
function startNextSet() {
    currentSet += 1;
    setCountDisplay.textContent = `${currentSet} / ${plannedSets}`;
    repCountDisplay.textContent = '0';
    repCountInlineDisplay.textContent = '0';
    motivationDisplay.textContent = '';
    motivationLevel = 0;
    nextSetBtn?.classList.add('hidden');
    resetExercise(); // reset backend state
}

/**
 * Update UI with backend response (add motivation and set logic)
 */
function updateUI(data) {
    const reps = data.repetitions || 0;
    repCountDisplay.textContent = reps;
    if (repCountInlineDisplay) repCountInlineDisplay.textContent = reps;

    // Auto-advance sets when rep target is reached
    if (plannedReps > 0 && reps >= plannedReps && currentSet < plannedSets) {
        startNextSet();
        return;
    }

    // Auto-open save progress modal when all sets are completed
    if (plannedReps > 0 && reps >= plannedReps && currentSet >= plannedSets && !didAutoOpenSaveModal) {
        didAutoOpenSaveModal = true;
        openProgressModal();
        return;
    }

    // Update current state
    currentStateDisplay.textContent = data.state || 'Unknown';
    if (data.state === 'OPEN') {
        currentStateDisplay.style.color = '#10b981';
    } else if (data.state === 'CLOSED') {
        currentStateDisplay.style.color = '#dc3545';
    } else {
        currentStateDisplay.style.color = '#e11d48';
    }

    // Show feedback if state changed
    if (data.feedback && data.state_changed) {
        showFeedback(data.feedback, 'success');
        if (audioEnabled) speakFeedback(data.feedback);
    }

    // Motivational phrases at milestones
    if (motivationDisplay && plannedReps > 0) {
        const progress = reps / plannedReps;
        if (progress >= 0.5 && motivationLevel < 1) {
            motivationLevel = 1;
            motivationDisplay.textContent = MOTIVATION_PHRASES[Math.floor(Math.random() * MOTIVATION_PHRASES.length)];
            if (audioEnabled) speakFeedback(motivationDisplay.textContent);
        } else if (progress >= 0.8 && motivationLevel < 2) {
            motivationLevel = 2;
            motivationDisplay.textContent = 'Konti na lang!';
            if (audioEnabled) speakFeedback(motivationDisplay.textContent);
        } else if (reps >= plannedReps && motivationLevel < 3) {
            motivationLevel = 3;
            motivationDisplay.textContent = 'Set complete!';
            if (audioEnabled) speakFeedback(motivationDisplay.textContent);
            // Show Next Set or finish
            if (currentSet < plannedSets) {
                nextSetBtn?.classList.add('hidden');
            } else {
                motivationDisplay.textContent += ' All sets done!';
            }
        }
    }
}

/**
 * Display feedback message to user
 */
function showFeedback(message, type = 'info') {
    feedbackBox.innerHTML = `<p>${message}</p>`;
    feedbackBox.classList.remove('success', 'error', 'info');
    if (type === 'success') {
        feedbackBox.classList.add('success');
    } else if (type === 'error') {
        feedbackBox.classList.add('error');
    } else {
        feedbackBox.classList.add('info');
    }
}

/**
 * Speak feedback using Web Speech API
 */
function speakFeedback(text) {
    // Check if browser supports speech synthesis
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;  // Normal speed
        utterance.pitch = 1.0;  // Normal pitch
        utterance.volume = 1.0;  // Full volume
        
        // Speak
        window.speechSynthesis.speak(utterance);
    }
}

/**
 * Reset exercise state and counter
 */
async function resetExercise() {
    try {
        const response = await fetch(`${BACKEND_URL}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exercise_type: currentExercise
            })
        });
        
        if (response.ok) {
            repCountDisplay.textContent = '0';
            currentStateDisplay.textContent = 'Ready';
            showFeedback('Counter reset!', 'success');
        }
        
    } catch (error) {
        console.error('Error resetting:', error);
        showFeedback('Error resetting counter', 'error');
    }
}

/**
 * Handle exercise type change
 */
function onExerciseChange(event) {
    currentExercise = event.target.value;
    resetExercise();
    
    const exerciseNames = {
        'open_close': 'Hand Open/Close',
        'pinch': 'Thumb-Index Pinch'
    };
    
    showFeedback(`Switched to: ${exerciseNames[currentExercise]}`, 'info');
}

/**
 * Handle audio toggle
 */
function onAudioToggle(event) {
    audioEnabled = event.target.checked;
    showFeedback(
        audioEnabled ? 'Audio feedback enabled' : 'Audio feedback muted',
        'info'
    );
}

// Helper function to draw connectors (from MediaPipe)
function drawConnectors(ctx, landmarks, connections, style) {
    connections.forEach(([start, end]) => {
        const startPoint = landmarks[start];
        const endPoint = landmarks[end];
        
        ctx.beginPath();
        ctx.moveTo(startPoint.x * ctx.canvas.width, startPoint.y * ctx.canvas.height);
        ctx.lineTo(endPoint.x * ctx.canvas.width, endPoint.y * ctx.canvas.height);
        ctx.strokeStyle = style.color;
        ctx.lineWidth = style.lineWidth;
        ctx.stroke();
    });
}

// Helper function to draw landmarks (from MediaPipe)
function drawLandmarks(ctx, landmarks, style) {
    landmarks.forEach(landmark => {
        ctx.beginPath();
        ctx.arc(
            landmark.x * ctx.canvas.width,
            landmark.y * ctx.canvas.height,
            style.radius,
            0,
            2 * Math.PI
        );
        ctx.fillStyle = style.color;
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = style.lineWidth;
        ctx.stroke();
    });
}

// Hand connections definition (which landmarks connect to which)
const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4],  // Thumb
    [0, 5], [5, 6], [6, 7], [7, 8],  // Index finger
    [0, 9], [9, 10], [10, 11], [11, 12],  // Middle finger
    [0, 13], [13, 14], [14, 15], [15, 16],  // Ring finger
    [0, 17], [17, 18], [18, 19], [19, 20],  // Pinky
    [5, 9], [9, 13], [13, 17]  // Palm
];

console.log('HandAssist app.js loaded successfully!');