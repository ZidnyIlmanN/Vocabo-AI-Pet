# Models Directory

This directory stores trained computer vision weights for food card recognition.

- `best.pt`: Ultralytics YOLO model trained on the custom food dataset generated from `scripts/train_model.py`.
- If `best.pt` is not present, the prototype can automatically run in fallback detection mode using visual template / feature matching so you can test immediately.
