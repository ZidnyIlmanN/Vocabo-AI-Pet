"""
Webcam Verification Script.
Checks whether laptop webcam opens, queries resolution, and displays frame rate.
"""
import sys
import time

def test_webcam(camera_index: int = 0):
    print(f"Checking webcam access on index {camera_index}...")
    try:
        import cv2
    except ImportError:
        print("ERROR: OpenCV is not installed. Please run: pip install opencv-python")
        return False

    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"CAP_DSHOW failed, trying default backend on index {camera_index}...")
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"FAILED: Cannot open camera on index {camera_index}!")
        print("Tip: Check if another application (e.g. Teams, Zoom, Browser) is using the camera.")
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print("\nSUCCESS: Webcam detected and opened successfully!")
    print(f" - Resolution: {width} x {height}")
    print(f" - Reported FPS: {fps}")

    # Capture 5 test frames
    start = time.perf_counter()
    valid_frames = 0
    for _ in range(10):
        ret, frame = cap.read()
        if ret and frame is not None:
            valid_frames += 1

    elapsed = time.perf_counter() - start
    real_fps = valid_frames / elapsed if elapsed > 0 else 0
    print(f" - Capture test: {valid_frames}/10 frames in {elapsed:.2f}s ({real_fps:.1f} FPS)")

    cap.release()
    print("\nWebcam is ready for Interactive AI Pet Prototype.")
    return True


if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    success = test_webcam(idx)
    sys.exit(0 if success else 1)
