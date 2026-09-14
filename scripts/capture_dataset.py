"""
Webcam Food Dataset Capture Utility.
Captures training images of food cards using laptop webcam.
Usage:
    python scripts/capture_dataset.py --food rice_egg
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CATALOG_PATH = DATA_DIR / "food_catalog.json"
FOODS_DIR = DATA_DIR / "foods"


def get_valid_food_ids():
    if not CATALOG_PATH.exists():
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [item["id"] for item in data.get("foods", [])]


def capture_dataset(food_id: str, camera_index: int = 0):
    try:
        import cv2
    except ImportError:
        print("ERROR: OpenCV is not installed. Please install opencv-python.")
        sys.exit(1)

    target_dir = FOODS_DIR / food_id
    target_dir.mkdir(parents=True, exist_ok=True)

    # Find highest existing number
    existing = list(target_dir.glob("image_*.jpg"))
    max_idx = 0
    for p in existing:
        try:
            num = int(p.stem.split("_")[1])
            max_idx = max(max_idx, num)
        except (IndexError, ValueError):
            pass

    print(f"\n==========================================")
    print(f" Dataset Collector: {food_id.upper()}")
    print(f" Target folder: {target_dir}")
    print(f" Existing images: {len(existing)} (Next index: {max_idx + 1:03d})")
    print(f" Controls:")
    print(f"   [SPACE]  Capture image")
    print(f"   [Q/ESC]  Finish and exit")
    print(f"==========================================\n")

    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"ERROR: Could not open camera on index {camera_index}!")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    count = max_idx
    flash_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.02)
            continue

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        display = frame.copy()

        # Guide box in center
        bw, bh = int(w * 0.45), int(h * 0.70)
        bx1, by1 = (w - bw) // 2, (h - bh) // 2
        bx2, by2 = bx1 + bw, by1 + bh

        # White flash when captured
        if flash_frames > 0:
            display[:, :] = (255, 255, 255)
            flash_frames -= 1
        else:
            cv2.rectangle(display, (bx1, by1), (bx2, by2), (0, 255, 120), 2)
            cv2.putText(
                display,
                f"Hold card inside guide box",
                (bx1, by1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 120),
                2,
            )

        # Header info
        cv2.putText(
            display,
            f"Food: {food_id} | Saved: {count}",
            (16, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            display,
            "Press [SPACE] to capture | [Q] to quit",
            (16, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 200),
            1,
        )

        cv2.imshow("Food Dataset Collector", display)
        key = cv2.waitKey(1) & 0xFF

        if key in (27, ord("q"), ord("Q")):
            break
        elif key == 32:  # Spacebar
            count += 1
            filename = f"image_{count:03d}.jpg"
            out_file = target_dir / filename
            cv2.imwrite(str(out_file), frame)
            print(f"Captured: {out_file}")
            flash_frames = 3

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nFinished capturing. Total images in {food_id}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Food Dataset Capture Utility")
    parser.add_argument("--food", type=str, required=True, help="Food class ID (e.g. rice_egg, apple, noodles)")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()

    valid_ids = get_valid_food_ids()
    if valid_ids and args.food not in valid_ids:
        print(f"WARNING: '{args.food}' is not in food_catalog.json.")
        print(f"Available classes: {', '.join(valid_ids)}")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != "y":
            sys.exit(0)

    capture_dataset(args.food, args.camera)
