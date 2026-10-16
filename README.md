# Interactive AI Pet Food Vision Prototype

A software prototype for an interactive robotic pet smart toy. Validates the **Computer Vision + Food Card Recognition + Pet Behavior + 60 FPS Animated Eye System + English TTS Voice Response** pipeline using a standard laptop webcam.

---

## 🌟 Key Features

1. **2D Animated Eye System (60 FPS)**:
   - Built with Pygame for smooth, decoupled 60 FPS rendering.
   - Expressions: `IDLE`, `HAPPY`, `HUNGRY`, `SAD`, `LONELY`, `SURPRISED`, `SLEEPY`, `CONFUSED`.
   - Natural randomized blinking (2.5s–6.0s), saccades (looking around), and cheering bounce.
   - Priority queue: temporary events (`CORRECT_FOOD`, `WRONG_FOOD`, `FOOD_DETECTED`) override persistent states and return seamlessly.
2. **Vision & Food Card Recognition**:
   - OpenCV threaded frame capture with horizontal mirror for natural interaction.
   - Ultralytics YOLO model support (`yolo11n.pt` / `yolov8n.pt`).
   - Temporal detection stabilization: requires 5 consecutive frames above 70% confidence to confirm a food card.
   - Safe offline fallback with simulation support.
3. **Pet Emotional State Machine**:
   - Emotional moods: `HUNGRY`, `HAPPY`, `SAD`, `LONELY`, `SLEEPY`.
   - Numerical metrics: Hunger (0-100), Happiness (0-100), Energy (0-100).
   - Food request engine with natural English speech prompts.
4. **Offline English Text-To-Speech (TTS)**:
   - Thread-safe, non-blocking audio queue using Windows SAPI5 (`pyttsx3`).
   - Dialogue is strictly in child-friendly, warm English.
   - Interaction cooldown (3.0s) prevents repeated stuttering speech.

---

## 📁 Project Architecture

```text
Pely/
├── app/
│   ├── config.py                 # Central dataclass configuration & .env loader
│   ├── main.py                   # 60 FPS application coordinator
│   │
│   ├── vision/
│   │   ├── camera.py             # Threaded webcam capture & offline test pattern
│   │   ├── detector.py           # YOLO inference worker & simulation injector
│   │   └── stabilizer.py         # Consecutive frame temporal confirmation
│   │
│   ├── pet/
│   │   ├── state.py              # PetState machine & emotional metrics
│   │   ├── food_request.py       # FoodItem catalog & desire generator
│   │   └── behavior.py           # Food matching, cooldowns & English phrases
│   │
│   ├── eyes/
│   │   ├── states.py             # EyeState persistent emotions
│   │   ├── events.py             # EyeEvent priority & durations
│   │   ├── animations.py         # Easing functions, blink curves & vector math
│   │   └── renderer.py           # Independent 60 FPS vector eye & mouth renderer
│   │
│   ├── audio/
│   │   └── tts.py                # Asynchronous queue-based SAPI5 English TTS
│   ├── sensors/
│   │   └── touch.py              # TTP223 touch input via Arduino/ESP32 USB serial
│   │
│   └── ui/
│       └── dashboard.py          # Unified composite UI layout
│
├── data/
│   ├── food_catalog.json         # 5 target classes (rice_egg, fried_chicken, noodles, apple, milk)
│   ├── sample_cards/             # Phone-ready graphical cards (PNG)
│   └── foods/                    # Training dataset images
│
├── models/
│   └── README.md                 # Model weights directory (best.pt)
│
├── scripts/
│   ├── generate_sample_cards.py  # Generates phone cards & synthetic dataset
│   ├── capture_dataset.py        # Live webcam dataset collection utility
│   ├── train_model.py            # YOLO fine-tuning script
│   └── test_camera.py            # Quick webcam diagnostic script
│
├── tests/                        # Automated unit test suite
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Generate Smartphone Food Cards
Generate high-resolution graphical food cards ready to be opened on your smartphone screen:
```powershell
python scripts/generate_sample_cards.py
```
This generates 5 PNG cards in `data/sample_cards/`:
- `rice_egg.png` (Rice & Egg)
- `fried_chicken.png` (Fried Chicken)
- `noodles.png` (Noodles)
- `apple.png` (Apple)
- `milk.png` (Milk)

Transfer or open any of these images on your smartphone!

### 3. Verify Webcam Access
```powershell
python scripts/test_camera.py
```

### 4. Connect an Optional TTP223 Touch Sensor

Connect the TTP223 `OUT` pin to a digital input on an Arduino or ESP32, and connect
the sensor's power and ground to the microcontroller using its supported voltage.
Connect the microcontroller to the computer over USB. The microcontroller firmware
should send one line containing `TOUCH` on each new touch, at 9600 baud. For example,
an Arduino sketch can detect a touch transition like this:

```cpp
const int TOUCH_PIN = 2;
bool wasTouched = false;
unsigned long lastTouchTime = 0;
const unsigned long debounceMs = 250;

void setup() {
  pinMode(TOUCH_PIN, INPUT);
  Serial.begin(9600);
}

void loop() {
  bool isTouched = digitalRead(TOUCH_PIN) == HIGH;
  unsigned long now = millis();

  if (isTouched && !wasTouched && now - lastTouchTime >= debounceMs) {
    Serial.println("TOUCH");
    lastTouchTime = now;
  }

  wasTouched = isTouched;
  delay(10);
}
```

Set the serial port in `.env` (for example, `COM3` on Windows) and enable the sensor:

```dotenv
TOUCH_SENSOR_ENABLED=true
TOUCH_SENSOR_PORT=COM3
```

The app adds 20 happiness points per accepted touch, capped at 100, and plays the
same reaction as the on-screen pet click and **P** key. Keep the serial monitor closed
while the app is using the microcontroller port. Touch input is disabled by default.

### 5. Run the Prototype Application
```powershell
python -m app.main
```

---

## 🎮 Interactive Controls & Testing

While the application is running, you can test it either with your **smartphone screen in front of the laptop camera**, or using the **keyboard shortcuts**:

| Key | Action |
|---|---|
| `1` | Simulate presenting **Rice and Egg** card |
| `2` | Simulate presenting **Fried Chicken** card |
| `3` | Simulate presenting **Noodles** card |
| `4` | Simulate presenting **Apple** card |
| `5` | Simulate presenting **Milk** card |
| `R` | Pet chooses a **new food desire** / requests food |
| `P` | **Pet / Affection** (+15% Happiness, triggers happy reaction) |
| `Q` / `Esc` | Cleanly exit application |

---

## 📸 Dataset Collection & YOLO Training

### 1. Collect Custom Webcam Dataset
To train a model on custom cards or printed media:
```powershell
# Capture 30-50 photos per food class:
python scripts/capture_dataset.py --food rice_egg
python scripts/capture_dataset.py --food fried_chicken
python scripts/capture_dataset.py --food noodles
python scripts/capture_dataset.py --food apple
python scripts/capture_dataset.py --food milk
```
- Hold the card within the green guide frame.
- Press **[SPACE]** to capture an image.
- Press **[Q]** when done.

### 2. Fine-tune the YOLO Model
```powershell
python scripts/train_model.py --epochs 20 --model yolo11n.pt
```
Trained weights will automatically be saved to `models/best.pt` and used by the prototype on subsequent launches.

---

## 🧪 Running Automated Unit Tests
```powershell
python -m pytest tests/ -v
```
