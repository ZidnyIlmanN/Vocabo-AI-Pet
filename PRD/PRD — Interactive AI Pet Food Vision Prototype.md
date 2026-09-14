# PRD — Interactive AI Pet Food Vision Prototype

## 1. Project Overview

Build the first software prototype of an interactive robotic pet / smart toy.

The final product will be a physical plush-toy-style pet that behaves similarly to a virtual pet game such as Pou: the child can feed it, interact with it, pet it, and receive emotional responses.

For this initial development phase, DO NOT build or integrate physical robot hardware yet.

The goal of this phase is to validate the **computer vision + food recognition + pet response pipeline** using the laptop's built-in camera.

The laptop camera should be able to recognize a food card/image displayed on a smartphone screen. When a recognized food matches the food currently requested by the pet, the system should respond appropriately using English voice output.

---

# 2. Current Prototype Goal

Create a desktop/local application with the following interaction:

```text
Pet requests food
       ↓
Example:
"I'm feeling hungry.
I think I'd like some rice and egg."
       ↓
User displays a food card on a smartphone
       ↓
Laptop webcam captures the card
       ↓
Computer Vision detects the food
       ↓
System identifies the food category
       ↓
Compare detected food with requested food
       ↓
       ┌───────────────┐
       │               │
     CORRECT         WRONG
       │               │
       ↓               ↓
Happy response     Gentle correction
       │               │
       └───────┬───────┘
               ↓
        English voice output
```

The prototype must demonstrate that the core concept works before moving to physical hardware.

---

# 3. Product Language

IMPORTANT:

The pet's language must be **English**.

All user-facing pet dialogue, recognition feedback, and voice responses must be in English.

Do NOT use Indonesian for pet dialogue.

The codebase, variable names, comments, and documentation may remain in English.

Example pet dialogue:

### Correct food

> "Yay! That's exactly what I wanted! Thank you!"

### Wrong food

> "Hmm... that's not what I asked for. Can you try again?"

### Food detected

> "Oh, I see it!"

### Hungry state

> "I'm feeling hungry. I think I'd like some rice and egg."

The tone should feel friendly, cute, warm, and suitable for children.

Avoid overly robotic or formal wording.

---

# 4. Scope of This Phase

## IN SCOPE

1. Laptop webcam input
2. Food image/card recognition
3. Custom food dataset support
4. Food classification
5. Food request generation
6. Matching detected food against requested food
7. Basic pet state
8. English text responses
9. English text-to-speech
10. Simple visual interface
11. Local testing
12. Logging/debug information

## OUT OF SCOPE

Do NOT implement these yet:

- Raspberry Pi
- ESP32
- Servo motors
- Physical plush toy
- Physical touch sensor
- Battery system
- Physical speaker
- Microphone input
- Speech-to-text
- Full conversational AI
- LLM-based autonomous behavior
- Cloud backend
- Mobile application
- User authentication
- Production deployment

The current objective is purely to validate the **vision-to-response interaction**.

---

# 5. Recommended Technology Stack

Use a practical Python-based computer vision stack.

## Core

- Python 3.11+
- OpenCV
- Ultralytics YOLO
- NumPy

## Machine Learning

Use a lightweight YOLO model suitable for local laptop inference.

Prefer:

- YOLO11n / current lightweight Ultralytics model if supported by the installed environment

The model should be trainable/fine-tunable using a custom dataset.

IMPORTANT:

Do not assume that a pretrained generic YOLO model can reliably recognize our custom food cards.

The application must be designed so that we can later train the model using our own food-card images.

---

# 6. Custom Food Dataset Architecture

The food images will be created manually by the project team.

The application must NOT hard-code food recognition around the initial example.

Create a configurable food catalog.

Example:

```text
data/
├── foods/
│   ├── rice_egg/
│   ├── fried_chicken/
│   ├── noodles/
│   ├── apple/
│   └── milk/
│
└── food_catalog.json
```

Example catalog:

```json
{
  "foods": [
    {
      "id": "rice_egg",
      "name": "Rice and Egg",
      "aliases": ["rice egg", "egg rice"],
      "image_folder": "data/foods/rice_egg"
    },
    {
      "id": "fried_chicken",
      "name": "Fried Chicken",
      "aliases": ["chicken"],
      "image_folder": "data/foods/fried_chicken"
    }
  ]
}
```

The system should use stable IDs internally.

Use human-readable English names for display and voice output.

---

# 7. Food Card Concept

The intended input is NOT a physical food object.

The user will initially display a food image/card on a smartphone screen.

Example:

```text
Smartphone
┌─────────────────────┐
│                     │
│        🍚 🍳         │
│                     │
│     RICE & EGG      │
│                     │
└─────────────────────┘
          ↓
      Laptop Camera
```

The computer vision pipeline must therefore work with:

- smartphone screen
- printed card
- custom-designed food card

as much as reasonably possible.

The first priority is smartphone-screen testing.

---

# 8. Vision Pipeline

Implement the following pipeline:

```text
Laptop Webcam
      ↓
OpenCV Frame Capture
      ↓
Preprocessing
      ↓
YOLO Inference
      ↓
Detected Food
      ↓
Confidence Filtering
      ↓
Food ID
      ↓
Application Logic
```

The system should display the webcam feed in real time.

Draw the detection bounding box around the detected food card.

Display:

```text
Food: Rice and Egg
Confidence: 94%
```

Example:

```text
┌──────────────────────────────┐
│                              │
│       [ FOOD CARD ]          │
│                              │
│       Rice and Egg           │
│       Confidence: 94%        │
│                              │
└──────────────────────────────┘
```

---

# 9. Confidence Threshold

Do not accept every detection.

Implement a configurable confidence threshold.

Example:

```python
CONFIDENCE_THRESHOLD = 0.70
```

If confidence is below the threshold:

```text
No reliable food detected.
```

The pet should not incorrectly react to uncertain predictions.

Make the threshold configurable through a config file or environment variable.

---

# 10. Temporal Detection Stabilization

Avoid triggering a response from a single unstable frame.

For example, require the same food prediction to appear consistently across multiple frames.

Example:

```text
Frame 1 → Rice and Egg
Frame 2 → Rice and Egg
Frame 3 → Rice and Egg
Frame 4 → Rice and Egg
Frame 5 → Rice and Egg
```

Then consider the food confirmed.

Implement a simple temporal confirmation mechanism.

Example:

```python
REQUIRED_CONSECUTIVE_FRAMES = 5
```

This value should be configurable.

---

# 11. Pet State

Implement a minimal state machine.

Initial states:

```text
HAPPY
HUNGRY
SAD
LONELY
```

For this first prototype, the most important state is:

```text
HUNGRY
```

Example:

```text
Pet State:
HUNGRY

Requested Food:
Rice and Egg
```

The pet should request a specific food.

Example:

> "I'm feeling hungry. I think I'd like some rice and egg."

---

# 12. Food Request Logic

Create a food request system.

Example:

```python
requested_food = "rice_egg"
```

The system should then wait for the user to show a food card.

When the vision system detects:

```text
rice_egg
```

compare:

```text
requested_food == detected_food
```

If true:

```text
CORRECT
```

Otherwise:

```text
WRONG
```

---

# 13. Correct Interaction

When the user shows the correct food:

```text
Pet State:
HUNGRY

Requested:
Rice and Egg

Detected:
Rice and Egg

Result:
CORRECT
```

Trigger:

1. Visual feedback
2. State update
3. English voice response

Example response:

> "Yay! That's exactly what I wanted! Thank you!"

Then update:

```text
HUNGRY → HAPPY
```

Optionally:

```text
hunger -= 30
happiness += 20
```

The numerical values should be configurable.

---

# 14. Incorrect Interaction

Example:

```text
Requested:
Rice and Egg

Detected:
Fried Chicken
```

The pet should respond gently.

Example:

> "Hmm... that's not what I asked for. Can you try again?"

Do not immediately punish the user.

Keep the interaction child-friendly.

The pet should remain:

```text
HUNGRY
```

and continue waiting for the correct food.

---

# 15. Text-to-Speech

Implement English TTS.

The architecture should be:

```text
Pet Logic
    ↓
Response Text
    ↓
TTS Engine
    ↓
Audio Output
```

Prefer an implementation that works locally/offline if practical.

Possible options:

- Piper TTS
- pyttsx3
- another lightweight local TTS solution

If offline TTS quality is insufficient, structure the application so that a cloud TTS provider can be added later without changing the pet logic.

Create a dedicated abstraction such as:

```python
class TTSService:
    def speak(self, text: str):
        ...
```

Do not couple the entire application directly to one TTS provider.

---

# 16. Pet Personality

The pet should have a consistent personality.

Personality:

- Cute
- Friendly
- Slightly playful
- Child-safe
- Encouraging
- Not overly verbose

Examples:

Correct:

> "Yummy! Thank you!"

Wrong:

> "Hmm... not quite! Let's try again."

Hungry:

> "My tummy is getting hungry!"

Lonely:

> "I miss playing with you."

Happy:

> "I'm having so much fun!"

Avoid phrases that are scary, aggressive, or emotionally manipulative.

---

# 17. User Interface

Create a simple desktop UI.

The UI should contain:

### Camera Preview

Large webcam preview.

### Pet Status

Example:

```text
PET STATUS
────────────
Mood: Hungry
Hunger: 72%
Happiness: 65%
Energy: 80%
```

### Current Request

```text
I want:
🍚 Rice and Egg
```

### Vision Result

```text
Detected:
Rice and Egg

Confidence:
94%

Status:
✓ Correct Food
```

### Event Log

Example:

```text
14:20:03 Camera started
14:20:08 Food detected: rice_egg
14:20:09 Confidence: 0.94
14:20:10 Food confirmed
14:20:10 Correct food
14:20:10 Pet response triggered
```

Keep the UI simple and functional.

Do not spend excessive time on visual design in this phase.

---

# 18. Suggested Project Structure

Use a modular architecture.

Suggested structure:

```text
interactive-pet/
│
├── app/
│   ├── main.py
│   │
│   ├── vision/
│   │   ├── camera.py
│   │   ├── detector.py
│   │   └── stabilizer.py
│   │
│   ├── pet/
│   │   ├── state.py
│   │   ├── behavior.py
│   │   └── food_request.py
│   │
│   ├── audio/
│   │   └── tts.py
│   │
│   ├── ui/
│   │   └── dashboard.py
│   │
│   └── config.py
│
├── data/
│   ├── foods/
│   └── food_catalog.json
│
├── models/
│   └── README.md
│
├── scripts/
│   ├── capture_dataset.py
│   ├── train_model.py
│   └── test_camera.py
│
├── logs/
│
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

Keep components modular so they can later be replaced or extended.

---

# 19. Dataset Collection Utility

Create a simple utility for collecting training images using the laptop webcam.

Example command:

```bash
python scripts/capture_dataset.py --food rice_egg
```

The utility should:

1. Open the webcam
2. Show the camera preview
3. Allow the user to capture images
4. Save them into the correct dataset directory
5. Number the images automatically

Example:

```text
data/foods/rice_egg/
├── image_001.jpg
├── image_002.jpg
├── image_003.jpg
└── ...
```

This is important because the team will create and iterate on its own food cards.

---

# 20. Training Utility

Create a training script that can train the vision model on the custom dataset.

Example:

```bash
python scripts/train_model.py
```

The training configuration should be easy to modify.

Document:

- dataset structure
- class names
- train/validation split
- number of epochs
- image size
- model used
- output location

Do not hard-code absolute Windows paths.

---

# 21. Initial Food Classes

For the first test, use a small number of food classes.

Example:

```text
rice_egg
fried_chicken
noodles
apple
milk
```

The architecture must support adding more classes without rewriting application logic.

---

# 22. Testing Scenarios

The implementation must support these test cases.

## Test 1 — Correct Food

Requested:

```text
Rice and Egg
```

Show:

```text
Rice and Egg card
```

Expected:

```text
Detected: Rice and Egg
Result: Correct
Pet becomes Happy
English voice response
```

---

## Test 2 — Wrong Food

Requested:

```text
Rice and Egg
```

Show:

```text
Apple card
```

Expected:

```text
Detected: Apple
Result: Wrong
Pet remains Hungry
English voice response
```

---

## Test 3 — No Food

Show nothing / normal room.

Expected:

```text
No food detected
No response triggered
```

---

## Test 4 — Low Confidence

Show an unclear/partially obscured food card.

Expected:

```text
Low confidence
No interaction triggered
```

---

## Test 5 — Temporary Detection

Move the card quickly through the camera.

Expected:

The system should NOT immediately trigger a response from one unstable frame.

---

# 23. Important UX Requirement

The system should avoid repeatedly speaking every frame.

BAD:

```text
Rice detected!
Rice detected!
Rice detected!
Rice detected!
Rice detected!
```

GOOD:

```text
Food detected
      ↓
Confirmation
      ↓
ONE interaction event
      ↓
Voice response
      ↓
Cooldown
```

Implement an interaction cooldown.

Example:

```python
RESPONSE_COOLDOWN_SECONDS = 3
```

Make it configurable.

---

# 24. Error Handling

The application must gracefully handle:

- Camera unavailable
- Camera permission denied
- Model file missing
- Invalid dataset
- No food detected
- Low confidence detection
- TTS failure
- Missing configuration
- Invalid food ID

Do not crash the whole application for normal runtime issues.

Show useful error messages.

---

# 25. Configuration

Use a centralized configuration system.

Example:

```text
CONFIDENCE_THRESHOLD=0.70
REQUIRED_CONSECUTIVE_FRAMES=5
RESPONSE_COOLDOWN_SECONDS=3
CAMERA_INDEX=0
```

Do not scatter magic numbers throughout the code.

---

# 26. Development Principles

Follow these principles:

1. Keep the implementation simple.
2. Avoid unnecessary frameworks.
3. Prefer modular components.
4. Avoid premature AI complexity.
5. Make all configurable values easy to change.
6. Keep vision and pet logic independent.
7. Keep TTS behind an abstraction.
8. Do not hard-code food classes in multiple places.
9. Make the system easy for another developer to understand.
10. Prioritize a working local prototype over production-level infrastructure.

---

# 27. Future Compatibility

The architecture should make it possible to later replace:

```text
Laptop Webcam
```

with:

```text
Raspberry Pi Camera
```

and replace:

```text
Laptop Speaker
```

with:

```text
Physical Speaker
```

and add:

```text
ESP32
↓
Servo
↓
Physical Pet Movement
```

without rewriting the core pet behavior.

Future architecture:

```text
             ┌────────────────────┐
             │    PET ENGINE      │
             │                    │
             │ State + Behavior   │
             └─────────┬──────────┘
                       │
            ┌──────────┼──────────┐
            ↓          ↓          ↓
         Vision      Audio      Sensors
            │          │          │
         Camera      Speaker    ESP32
                                  │
                             Servo / Touch
```

---

# 28. Definition of Done

This phase is considered complete when:

- [ ] Laptop webcam successfully opens.
- [ ] Webcam feed is visible in the application.
- [ ] Custom food dataset structure exists.
- [ ] At least 3–5 food classes can be configured.
- [ ] A custom YOLO-based food recognition model can be trained.
- [ ] The model can recognize the custom food cards.
- [ ] Smartphone-screen food cards can be detected.
- [ ] Confidence score is displayed.
- [ ] Temporal detection stabilization works.
- [ ] Pet can request a specific food.
- [ ] Detected food is compared against the requested food.
- [ ] Correct food triggers a happy response.
- [ ] Wrong food triggers a gentle response.
- [ ] Pet responses are spoken in English.
- [ ] Response cooldown prevents repeated speech.
- [ ] Basic pet state is implemented.
- [ ] Dataset collection utility works.
- [ ] Training script works.
- [ ] README contains setup and testing instructions.
- [ ] No physical robot hardware is required.

---

# 29. Expected Demo

The final demo should look approximately like this:

```text
┌─────────────────────────────────────────────┐
│             INTERACTIVE PET                │
├───────────────────────┬─────────────────────┤
│                       │ PET                 │
│                       │                     │
│   LAPTOP CAMERA       │ Mood: Hungry        │
│                       │ Hunger: 72%         │
│   ┌───────────────┐   │ Happiness: 65%      │
│   │ 🍚 🍳         │   │                     │
│   │ Rice & Egg    │   │ Wants:              │
│   └───────────────┘   │ Rice and Egg        │
│                       │                     │
│ Detected:             │                     │
│ Rice and Egg          │                     │
│ Confidence: 94%      │                     │
│                       │                     │
│ ✓ CORRECT FOOD       │                     │
└───────────────────────┴─────────────────────┘
```

The pet then speaks:

> "Yay! That's exactly what I wanted! Thank you!"

---

# 30. First Development Priority

Do not implement everything at once.

Build in this order:

### Step 1
Verify laptop webcam access.

### Step 2
Create the food dataset structure.

### Step 3
Create the dataset capture utility.

### Step 4
Train a small custom food recognition model.

### Step 5
Run real-time webcam detection.

### Step 6
Add food confidence and temporal stabilization.

### Step 7
Add requested-food logic.

### Step 8
Add correct/wrong response logic.

### Step 9
Add English TTS.

### Step 10
Build the simple dashboard UI.

Only proceed to the next step after the previous step works.

---

# 31. Agent Behavior

You are acting as the lead software engineer for this prototype.

Before making major architectural changes:

- inspect the existing repository
- identify the operating system
- inspect installed Python version
- inspect existing dependencies
- reuse existing infrastructure when appropriate
- avoid replacing working components unnecessarily

When implementing, explain briefly:

1. What you are changing
2. Why it is needed
3. How to run/test it

Do not introduce unnecessary dependencies.

If a dependency is required, explain why before adding it.

If there are multiple viable approaches, choose the simplest approach that satisfies the requirements.

The immediate goal is a **working, testable computer-vision prototype**, not a production system.

---

# 32. Final Success Criteria

At the end of this phase, I should be able to:

1. Start the application on my laptop.
2. See the laptop camera feed.
3. Show a custom food card from my smartphone.
4. The system recognizes the food.
5. The system displays the detected food and confidence.
6. The pet knows which food it currently wants.
7. The system determines whether the shown food is correct.
8. The pet responds accordingly.
9. The pet speaks the response in English.
10. I can add new custom food cards/classes later without redesigning the entire system.

Start by inspecting the repository and environment, then implement the project incrementally according to the development priority above.