"""
Gesture-controlled PowerPoint presenter.

Use hand gestures (0-5 fingers) to control a PowerPoint slideshow.

Controls:
0 → Exit slideshow (Esc)
1 → Screenshot
2 → Start slideshow (F5)
3 → Previous slide (Left)
4 → Next slide (Right)
5 → Open PowerPoint file (if provided via --pptx)

IMPORTANT:
- PyAutoGUI sends keystrokes to the ACTIVE window.
- Make sure PowerPoint is focused before controlling slides.
- For best results, use a plain background and ensure good lighting.
"""

import argparse
import os
import time

import cv2
import mediapipe as mp
import pyautogui
from mediapipe.tasks.python import vision

from gesture_utils import fingers_up, GestureStabilizer, GESTURE_NAMES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "hand_landmarker.task")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17),
]


def take_screenshot():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filename = os.path.join(
        SCREENSHOT_DIR, f"screenshot_{int(time.time())}.png"
    )
    pyautogui.screenshot(filename)
    return filename


def build_gesture_actions(pptx_path=None):
    """Map finger counts → PowerPoint actions."""

    return {
        0: {
            "label": "Exit Slideshow",
            "color": (60, 60, 255),
            "run": lambda: pyautogui.press("esc")
        },

        1: {
            "label": "Screenshot Saved",
            "color": (255, 255, 0),
            "run": take_screenshot
        },

        2: {
            "label": "Start Slideshow (F5)",
            "color": (255, 0, 255),
            "run": lambda: pyautogui.press("f5")
        },

        3: {
            "label": "Previous Slide",
            "color": (0, 200, 255),
            "run": lambda: pyautogui.press("left")
        },

        4: {
            "label": "Next Slide",
            "color": (0, 255, 0),
            "run": lambda: pyautogui.press("right")
        },

        5: {
            "label": "Open PowerPoint File",
            "color": (0, 255, 255),
            "run": lambda: os.startfile(pptx_path) if pptx_path else None
        },
    }


def draw_hand(frame, hand_landmarks, w, h):
    for a, b in HAND_CONNECTIONS:
        x1, y1 = int(hand_landmarks[a].x * w), int(hand_landmarks[a].y * h)
        x2, y2 = int(hand_landmarks[b].x * w), int(hand_landmarks[b].y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

    for lm in hand_landmarks:
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (x, y), 5, (255, 0, 255), -1)


def draw_overlay(frame, w, h, status_text, status_color, fps, agreement_ratio, show_legend):
    cv2.rectangle(frame, (0, 0), (w, 70), (20, 20, 20), -1)

    cv2.putText(frame, status_text, (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)

    cv2.putText(frame, f"FPS: {fps:.0f}", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # stability bar
    bar_x, bar_y, bar_w, bar_h = w - 160, 25, 130, 14
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + bar_w, bar_y + bar_h), (90, 90, 90), 1)

    fill_w = int(bar_w * min(agreement_ratio, 1.0))
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + fill_w, bar_y + bar_h), (0, 220, 0), -1)

    cv2.putText(frame, "lock-in", (bar_x, bar_y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1)

    if not show_legend:
        return

    legend_y = h - 10 - 18 * len(GESTURE_NAMES)

    cv2.rectangle(frame, (0, legend_y - 10), (260, h), (20, 20, 20), -1)

    for count in sorted(GESTURE_NAMES):
        cv2.putText(
            frame,
            f"{count}: {GESTURE_NAMES[count]}",
            (10, legend_y + 18 * count + 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--min-confidence", type=float, default=0.7)
    parser.add_argument("--buffer-size", type=int, default=8)
    parser.add_argument("--min-agreement", type=int, default=6)
    parser.add_argument("--no-legend", action="store_true")
    parser.add_argument("--pptx", type=str, default=None,
                        help="Path to PowerPoint file to open with gesture 5")

    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print("Missing model. Run setup_models.py first.")
        return

    base_options = mp.tasks.BaseOptions(model_asset_path=MODEL_PATH)

    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=args.min_confidence,
        min_hand_presence_confidence=args.min_confidence,
        min_tracking_confidence=args.min_confidence,
    )

    hand_landmarker = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print("Cannot open webcam")
        return

    actions = build_gesture_actions(args.pptx)
    stabilizer = GestureStabilizer(
        buffer_size=args.buffer_size,
        min_agreement=args.min_agreement
    )

    status_text = "Show a gesture..."
    status_color = (200, 200, 200)

    flash_until = 0
    prev_time = time.time()

    show_legend = not args.no_legend

    print("=" * 50)
    print("🎯 POWERPOINT GESTURE CONTROLLER")
    print("=" * 50)
    print("Controls:")
    print("  ✊ Fist (0)   : Exit slideshow")
    print("  ☝️  One (1)    : Screenshot")
    print("  ✌️  Two (2)    : Start slideshow (F5)")
    print("  🤟 Three (3)   : Previous slide")
    print("  ✋ Four (4)     : Next slide")
    print("  🖐️  Five (5)    : Open PowerPoint file")
    print("-" * 50)
    print("Controls:")
    print("  Q - Quit")
    print("  L - Toggle legend")
    print("=" * 50)
    print("💡 TIP: Make sure PowerPoint window is active before gesturing!")
    print("=" * 50)

    print("Running... Press Q to quit.")

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = hand_landmarker.detect(mp_image)

        reading = GestureStabilizer.NO_HAND

        if result.hand_landmarks:
            hand_landmarks = result.hand_landmarks[0]
            draw_hand(frame, hand_landmarks, w, h)

            reading = sum(fingers_up(hand_landmarks))

        fired = stabilizer.update(reading)

        if fired is not None and fired in actions:
            action = actions[fired]
            action["run"]()
            status_text = action["label"]
            status_color = action["color"]
            flash_until = time.time() + 1.2  # Slightly longer feedback

        if time.time() > flash_until:
            status_color = (200, 200, 200)
            status_text = (
                "Show a hand gesture..."
                if reading == GestureStabilizer.NO_HAND
                else f"Holding: {reading} fingers"
            )

        agreement_ratio = (
            stabilizer.buffer.count(reading) /
            max(len(stabilizer.buffer), 1)
        )

        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        draw_overlay(
            frame, w, h,
            status_text,
            status_color,
            fps,
            agreement_ratio,
            show_legend
        )

        cv2.imshow("PowerPoint Gesture Controller", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("l"):
            show_legend = not show_legend

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()