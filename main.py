import cv2
import mediapipe as mp
import pyautogui
import time
from mediapipe.tasks.python import vision
import os
import webbrowser

# Resolve the hand landmark model relative to this script so execution is cwd-independent.
model_path = os.path.join(os.path.dirname(__file__), "models/hand_landmarker.task")

if not os.path.exists(model_path):
    print(f"Error: Model file not found at {model_path}")
    print("Please run: python3 setup_models.py")
    exit(1)

# Configure a single-hand detector tuned for stable real-time tracking.
base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
hand_landmarker = vision.HandLandmarker.create_from_options(options)

# Open the default webcam (index 0).
cap = cv2.VideoCapture(0)

last_time = 0
cooldown = 2  # Prevent repeated key presses

def fingers_up(hand_landmarks):
    """Detect which fingers are up based on landmarks"""
    tips = [8, 12, 16, 20]   # Fingertip indices
    pips = [6, 10, 14, 18]   # PIP joint indices

    fingers = []
    for tip, pip in zip(tips, pips):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    detection_result = hand_landmarker.detect(mp_image)
    gesture = "Waiting..."

    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # Draw landmarks
            for landmark in hand_landmarks:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 5, (255, 0, 255), -1)

            # Draw connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (5, 6), (6, 7), (7, 8),
                (9, 10), (10, 11), (11, 12),
                (13, 14), (14, 15), (15, 16),
                (17, 18), (18, 19), (19, 20),
                (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)
            ]
            for start_idx, end_idx in connections:
                start, end = hand_landmarks[start_idx], hand_landmarks[end_idx]
                x1, y1 = int(start.x * w), int(start.y * h)
                x2, y2 = int(end.x * w), int(end.y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

            # Gesture logic
            fingers = fingers_up(hand_landmarks)
            total = fingers.count(1)
            current_time = time.time()

            if current_time - last_time > cooldown:
                if total == 5:
                    webbrowser.open("https://slides.google.com")
                    gesture = "Opening Google Slides"
                elif total == 4:
                    pyautogui.press("right")
                    gesture = "Next Slide"
                elif total == 3:
                    pyautogui.press("left")
                    gesture = "Previous Slide"
                elif total == 2:
                    pyautogui.press("f5")
                    gesture = "Start Slideshow"
                elif total == 1:
                    filename = f"screenshot_{int(time.time())}.png"
                    pyautogui.screenshot(filename)
                    gesture = "Screenshot Saved"
                elif total == 0:
                    pyautogui.press("esc")
                    gesture = "Exit Slideshow"

                last_time = current_time

    cv2.putText(frame, gesture, (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Google Slides Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
