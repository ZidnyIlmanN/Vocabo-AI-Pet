"""
YOLO Food Card Recognition Training Utility.
Automates dataset splitting, bounding box generation, and fine-tuning lightweight YOLO model.
Usage:
    python scripts/train_model.py [--epochs 25] [--model yolo11n.pt]
"""
import argparse
import json
import os
from pathlib import Path
import random
import shutil
import sys
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CATALOG_PATH = DATA_DIR / "food_catalog.json"
FOODS_DIR = DATA_DIR / "foods"
MODELS_DIR = ROOT_DIR / "models"
YOLO_DATASET_DIR = DATA_DIR / "yolo_dataset"

MODELS_DIR.mkdir(parents=True, exist_ok=True)


def prepare_yolo_dataset(val_split: float = 0.2):
    """
    Scans data/foods/<food_id>/, assigns class IDs, generates YOLO format labels,
    and splits into train and val folders.
    """
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Missing {CATALOG_PATH}")

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    classes = [item["id"] for item in catalog.get("foods", [])]
    class_to_id = {name: idx for idx, name in enumerate(classes)}

    # Reset YOLO dataset directory
    if YOLO_DATASET_DIR.exists():
        shutil.rmtree(YOLO_DATASET_DIR)

    for split in ("train", "val"):
        (YOLO_DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (YOLO_DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    total_train = 0
    total_val = 0

    print("Preparing YOLO dataset structure...")
    for class_name, class_id in class_to_id.items():
        src_folder = FOODS_DIR / class_name
        if not src_folder.exists():
            continue

        images = list(src_folder.glob("*.jpg")) + list(src_folder.glob("*.png"))
        if not images:
            continue

        random.shuffle(images)
        val_count = max(1, int(len(images) * val_split))
        train_images = images[val_count:]
        val_images = images[:val_count]

        for split, img_list in [("train", train_images), ("val", val_images)]:
            for img_path in img_list:
                dest_img = YOLO_DATASET_DIR / "images" / split / f"{class_name}_{img_path.name}"
                shutil.copy(img_path, dest_img)

                # Generate bounding box label
                # Default box: centered bounding box (cx=0.5, cy=0.5, w=0.65, h=0.75)
                # matching the smartphone card capture guide
                dest_lbl = YOLO_DATASET_DIR / "labels" / split / f"{dest_img.stem}.txt"
                with open(dest_lbl, "w") as lf:
                    lf.write(f"{class_id} 0.5 0.5 0.65 0.75\n")

                if split == "train":
                    total_train += 1
                else:
                    total_val += 1

    print(f"Dataset split complete: {total_train} train images, {total_val} validation images.")

    # Create dataset.yaml
    yaml_content = {
        "path": str(YOLO_DATASET_DIR.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {idx: name for idx, name in enumerate(classes)},
    }

    yaml_path = YOLO_DATASET_DIR / "dataset.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_content, f, sort_keys=False)

    print(f"Generated YAML config: {yaml_path}")
    return yaml_path, classes


def train(epochs: int = 20, base_model: str = "yolo11n.pt", imgsz: int = 480):
    try:
        from ultralytics import YOLO
    except ImportError:
        print("ERROR: Ultralytics is not installed. Please run: pip install ultralytics")
        sys.exit(1)

    yaml_path, classes = prepare_yolo_dataset()

    print(f"\n==========================================")
    print(f" Starting YOLO Training")
    print(f" Base model: {base_model}")
    print(f" Classes ({len(classes)}): {', '.join(classes)}")
    print(f" Epochs: {epochs} | Image size: {imgsz}")
    print(f"==========================================\n")

    # If yolo11n.pt is not available locally, ultralytics will auto-download or we can fallback to yolov8n.pt
    try:
        model = YOLO(base_model)
    except Exception:
        print(f"Could not load {base_model}, falling back to yolov8n.pt...")
        model = YOLO("yolov8n.pt")

    import torch
    dev = "0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {dev} (CUDA available: {torch.cuda.is_available()})")

    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=8,
        device=dev,
        project="runs/food_detect",
        name="prototype_run",
        exist_ok=True,
    )

    # Copy best weights to models/best.pt
    best_weights = Path(model.trainer.best if hasattr(model, "trainer") and model.trainer else "runs/food_detect/prototype_run/weights/best.pt")
    target_weights = MODELS_DIR / "best.pt"

    if best_weights.exists():
        shutil.copy(best_weights, target_weights)
        print(f"\nSUCCESS: Trained model saved to: {target_weights.resolve()}")
    else:
        print(f"\nTraining completed. Inspect runs/ directory for weights.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Food Card YOLO Model")
    parser.add_argument("--epochs", type=int, default=15, help="Number of epochs")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="Base model (e.g. yolo11n.pt, yolov8n.pt)")
    parser.add_argument("--imgsz", type=int, default=480, help="Image size")
    args = parser.parse_args()

    train(epochs=args.epochs, base_model=args.model, imgsz=args.imgsz)
