# Gesture Control for PowerPoint

Control a PowerPoint presentation with hand gestures, using your webcam.
Built with MediaPipe Hand Landmarker, OpenCV, and PyAutoGUI.

![status](https://img.shields.io/badge/tests-9%20passing-brightgreen)

## How it works

A MediaPipe hand-landmark model tracks 21 points on your hand in real time.
The app counts how many fingers are raised (0–5) and maps that count to a
keyboard/browser action. To avoid misfires from a hand mid-transition
between poses, a short rolling buffer requires the same reading to "win" a
majority vote before any action fires (see `gesture_utils.GestureStabilizer`).

## Gesture chart

| Fingers up | Action              |
|------------|---------------------|
| 0 (fist)   | Exit slideshow (Esc)|
| 1          | Take a screenshot   |
| 2          | Start slideshow (F5)|
| 3          | Previous slide      |
| 4          | Next slide          |
| 5 (open palm) | Open PowerPoint file |

## Setup

```bash
pip install -r requirements.txt
python3 setup_models.py     # downloads the hand-tracking model (~7-9 MB)
python3 main.py [--pptx path/to/your/presentation.pptx]
```

Press `q` in the preview window to quit, `l` to toggle the on-screen legend.

## Usage

1. **Start the application**: `python3 main.py` 
2. **To open a specific presentation**: `python3 main.py --pptx "path/to/your/file.pptx"`
3. **Make sure PowerPoint is the active window** before gesturing
4. **Show gestures clearly** to your webcam:
   - ✋ 0 fingers (fist): Exit slideshow
   - ☝️ 1 finger: Take screenshot (saved to screenshots/ folder)
   - ✌️ 2 fingers: Start slideshow (presses F5)
   - 🤟 3 fingers: Previous slide (left arrow)
   - 🤌 4 fingers: Next slide (right arrow)
   - ✋ 5 fingers (open palm): Open the specified PowerPoint file

## Important: Window Focus

`pyautogui` sends keystrokes to whichever window has OS focus — not necessarily the preview window. **Click into your PowerPoint window first**, then keep gesturing; the preview window only needs to stay open and visible, it doesn't need to be focused.

## Troubleshooting

- **"Model file not found"** — run `python3 setup_models.py` first.
- **Gestures fire late or not at all** — increase `--min-confidence` if lighting is poor, or lower `--min-agreement` if it feels unresponsive (default requires 6 of the last 8 frames to agree).
- **5-finger/open-palm gesture feels unreliable** — make sure your whole hand (including thumb) is clearly visible and not against a cluttered background.
- **Nothing happens in PowerPoint** — see "Important: Window Focus" above.

## Customization

Adjust sensitivity with these flags:
- `--camera 1` - Use a different webcam
- `--no-legend` - Hide the legend overlay (useful when screen recording)
- `--buffer-size 10 --min-agreement 8` - Require longer, more confident holds
- `--min-confidence 0.8` - Increase detection confidence (helps in poor lighting)

## Project Structure

```
main.py              # Camera loop, MediaPipe wiring, on-screen UI
gesture_utils.py     # Pure-Python gesture logic (no camera/UI deps) — unit tested
setup_models.py      # Downloads & validates the hand_landmarker model
tests/               # Pytest suite for gesture_utils.py
screenshots/         # Where screenshots are saved (auto-created)
models/              # MediaPipe model files (auto-downloaded)
```

The core gesture recognition (`gesture_utils.py`) has zero dependencies on MediaPipe/OpenCV/PyAutoGUI — it only needs objects with `.x`/`.y` attributes — so the logic can be tested quickly without camera hardware.
