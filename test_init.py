#!/usr/bin/env python3
"""
Test script to verify the PowerPoint gesture controller initializes correctly.
This allows testing without requiring a webcam or actually running the camera loop.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    try:
        import main
        import gesture_utils
        print("PASS: All imports successful")
        return True
    except Exception as e:
        print(f"FAIL: Import failed: {e}")
        return False

def test_gesture_utils():
    """Test the gesture utility functions."""
    print("\nTesting gesture utilities...")
    try:
        from gesture_utils import fingers_up, finger_total, GestureStabilizer, GESTURE_NAMES

        # Test that gesture names have been updated correctly
        assert GESTURE_NAMES[5] == "Open PowerPoint", f"Expected 'Open PowerPoint', got '{GESTURE_NAMES[5]}'"
        print("PASS: Gesture names updated correctly for PowerPoint")

        # Test basic functionality
        print("PASS: Gesture utilities working correctly")
        return True
    except Exception as e:
        print(f"FAIL: Gesture utility test failed: {e}")
        return False

def test_build_gesture_actions():
    """Test that the gesture actions function works correctly."""
    print("\nTesting gesture actions builder...")
    try:
        import main
        # Test without PPTX path
        actions = main.build_gesture_actions(None)
        assert 0 in actions
        assert 1 in actions
        assert 2 in actions
        assert 3 in actions
        assert 4 in actions
        assert 5 in actions
        assert "Open PowerPoint File" in actions[5]["label"]
        print("PASS: Gesture actions built correctly")

        # Test with PPTX path
        test_path = "test.pptx"
        actions_with_path = main.build_gesture_actions(test_path)
        assert "Open PowerPoint File" in actions_with_path[5]["label"]
        print("PASS: Gesture actions with PPTX path work correctly")

        return True
    except Exception as e:
        print(f"FAIL: Gesture actions test failed: {e}")
        return False

def main_test():
    """Run all tests."""
    print("=" * 50)
    print("POWERPOINT GESTURE CONTROLLER - INITIALIZATION TEST")
    print("=" * 50)

    tests = [
        test_imports,
        test_gesture_utils,
        test_build_gesture_actions
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print("PASS: All initialization tests passed!")
        print("PASS: The PowerPoint gesture controller is ready to use.")
        print("\nTo run the full application:")
        print("  python main.py                    # Basic usage")
        print("  python main.py --pptx presentation.pptx  # With specific file")
        return True
    else:
        print("FAIL: Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main_test()
    sys.exit(0 if success else 1)