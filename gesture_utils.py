"""
gesture_utils.py

Core gesture-recognition logic, deliberately kept free of any MediaPipe/OpenCV
dependency. It only needs landmark-like objects exposing .x/.y attributes
(MediaPipe's NormalizedLandmark satisfies this, and so does a plain mock in
tests). Keeping this layer pure makes it fast to unit test and easy to reuse
in a different UI later.

Landmark indices follow the MediaPipe Hand Landmark model:
https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
"""

from collections import deque, Counter

# Fingertip / PIP-joint pairs for the 4 non-thumb fingers.
_TIP_IDS = [8, 12, 16, 20]
_PIP_IDS = [6, 10, 14, 18]

# Thumb is anatomically different (it bends sideways, not vertically), so it
# can't use the same tip-above-pip check as the other fingers. Instead we
# compare each point's distance to the pinky-MCP knuckle (landmark 17): when
# the thumb is folded into the palm it sits close to that knuckle; when
# extended it's far away. This works regardless of whether it's a left or
# right hand, or how the hand is rotated, which a simple x-coordinate
# comparison would not.
_THUMB_TIP = 4
_THUMB_IP = 3
_WRIST = 0
_PINKY_MCP = 17
_THUMB_MARGIN = 1.1  # require >10% farther, to avoid borderline flicker


def _dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def fingers_up(landmarks):
    """
    Given 21 hand landmarks, return a list of 5 ints (0 or 1):
    [thumb, index, middle, ring, pinky]
    """
    fingers = []
    for tip, pip in zip(_TIP_IDS, _PIP_IDS):
        fingers.append(1 if landmarks[tip].y < landmarks[pip].y else 0)

    pinky_mcp = landmarks[_PINKY_MCP]
    thumb_tip = landmarks[_THUMB_TIP]
    thumb_ip = landmarks[_THUMB_IP]
    thumb_extended = _dist(thumb_tip, pinky_mcp) > _dist(thumb_ip, pinky_mcp) * _THUMB_MARGIN
    fingers.insert(0, 1 if thumb_extended else 0)

    return fingers


def finger_total(landmarks):
    """Convenience wrapper: total fingers raised, 0-5."""
    return sum(fingers_up(landmarks))


class GestureStabilizer:
    """
    Smooths frame-by-frame finger counts into a single, deliberate action.

    Problem this solves: reading raw per-frame finger counts and firing on
    whichever value happens to be visible the instant a cooldown timer
    expires causes misfires while the hand is mid-transition between poses
    (e.g. 3 -> 4 fingers passes through unstable intermediate readings).

    Approach: keep a short rolling buffer of recent readings. Only fire when
    one value dominates the buffer (majority vote), and only fire ONCE per
    "hold" of that gesture -- the same gesture won't fire again until the
    buffer first settles on a different value (including "no hand" / -1).
    This mirrors how a person naturally uses the controller: show a pose,
    see it register, relax, show the next pose.
    """

    NO_HAND = -1

    def __init__(self, buffer_size=8, min_agreement=6):
        if min_agreement > buffer_size:
            raise ValueError("min_agreement cannot exceed buffer_size")
        self.buffer = deque(maxlen=buffer_size)
        self.min_agreement = min_agreement
        self._last_fired = None

    def update(self, value):
        """
        Feed in this frame's reading (an int 0-5, or NO_HAND if no hand was
        detected). Returns the value to act on if a new stable gesture was
        just locked in, otherwise None.
        """
        self.buffer.append(value)
        if len(self.buffer) < self.buffer.maxlen:
            return None

        winner, count = Counter(self.buffer).most_common(1)[0]
        if count < self.min_agreement:
            return None

        if winner == self.NO_HAND:
            self._last_fired = None
            return None

        if winner == self._last_fired:
            return None  # still holding the same pose that already fired

        self._last_fired = winner
        return winner

    def reset(self):
        self.buffer.clear()
        self._last_fired = None


# Human-readable names, kept separate from main.py's action callables so
# this module never needs to import pyautogui/webbrowser.
GESTURE_NAMES = {
    0: "Exit Slideshow",
    1: "Screenshot",
    2: "Start Slideshow",
    3: "Previous Slide",
    4: "Next Slide",
    5: "Open PowerPoint",
}
