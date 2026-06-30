"""
Download the MediaPipe hand_landmarker model used by main.py.

Run this once before main.py:
    python3 setup_models.py
"""

import os
import ssl
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# Real model file is several MB; anything drastically smaller is almost
# certainly an HTML/XML error page saved with a .task extension.
MIN_VALID_SIZE_BYTES = 1_000_000

MODELS = {
    # NOTE: the previous version of this script pointed at bucket
    # "mediapipe-assets", which never hosted this file (always 403/404),
    # and a GitHub release URL that no longer exists (404). These are the
    # current, correct paths per Google's official MediaPipe documentation.
    "hand_landmarker": [
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    ]
}


def is_corrupted(path):
    """Binary-safe check for an HTML/XML error page masquerading as a model file."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return True
    if size < MIN_VALID_SIZE_BYTES:
        return True
    with open(path, "rb") as f:
        head = f.read(512)
    return b"<Error>" in head or b"<?xml" in head or b"<html" in head.lower()


def download(url, dest):
    """Try a normal HTTPS request first; only fall back to an unverified
    SSL context if certificate verification is actually the problem, rather
    than disabling verification globally up front."""
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except ssl.SSLCertVerificationError:
        print("  Certificate verification failed, retrying without verification...")
        ctx = ssl._create_unverified_context()
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, dest)
        urllib.request.install_opener(urllib.request.build_opener())  # restore default
        return True


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    for name, urls in MODELS.items():
        model_path = os.path.join(MODELS_DIR, f"{name}.task")

        if os.path.exists(model_path):
            if is_corrupted(model_path):
                print(f"x Existing {name}.task looks invalid/corrupted, re-downloading...")
                os.remove(model_path)
            else:
                print(f"OK {name}.task already present and looks valid, skipping.")
                continue

        downloaded = False
        for url in urls:
            print(f"Downloading {name} from {url} ...")
            try:
                download(url, model_path)
                if is_corrupted(model_path):
                    print("  Downloaded file failed validation, trying next source...")
                    os.remove(model_path)
                    continue
                size_mb = os.path.getsize(model_path) / (1024 * 1024)
                print(f"OK Downloaded {name}.task ({size_mb:.1f} MB)")
                downloaded = True
                break
            except Exception as e:
                print(f"  Failed: {e}")

        if not downloaded:
            print(f"x Could not download {name} from any source. Check your network/firewall.")


if __name__ == "__main__":
    main()
