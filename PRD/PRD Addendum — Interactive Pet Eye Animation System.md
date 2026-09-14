# PRD Addendum — Interactive Pet Eye Animation System

## 1. Feature Overview

Add a real-time animated eye system to the Interactive AI Pet prototype.

The animated eyes will be displayed directly on the laptop screen and will act as the visual face of the virtual pet.

The eye animation must react to the pet's current state and interaction events.

The objective is to make the prototype feel like an actual interactive pet even before the physical plush toy hardware is implemented.

---

# 2. Core Concept

The laptop screen should display:

```text
┌─────────────────────────────────────┐
│                                     │
│           ●●        ●●              │
│                                     │
│                ╭──╮                 │
│                 ╰──╯                │
│                                     │
│        "I'm feeling hungry..."      │
│                                     │
└─────────────────────────────────────┘
```

The eyes should behave like the eyes of a cute digital pet.

They should:

- blink naturally
- look around occasionally
- change expression
- react to food
- react to incorrect food
- react to interaction
- become sleepy when tired
- look sad when lonely
- look happy after receiving the correct food

Do not make the eyes static.

---

# 3. Design Direction

The visual style should be:

- Cute
- Minimal
- Friendly
- Child-oriented
- Modern
- Expressive
- Soft
- Easy to understand

Avoid:

- scary eyes
- realistic human eyes
- overly complex 3D graphics
- visually noisy UI
- aggressive animations
- overly robotic appearance

The eyes should feel like a **cute digital pet**, not a humanoid robot.

---

# 4. Recommended Implementation

For the laptop prototype, implement the eyes as a **2D animated UI component**.

Preferred approach:

### Option A — Pygame

Use Pygame if the application is primarily Python-based and needs smooth real-time animation.

### Option B — PySide6

Use PySide6 if the application UI is already being implemented with Qt.

The eye system must be implemented as an independent component so it can later be replaced or rendered on:

- OLED
- LCD
- LED matrix
- physical eye displays

Do not tightly couple the eye animation to the vision system.

---

# 5. Eye Animation Architecture

Use a state-driven animation system.

```text
                    PET STATE
                       │
                       ↓
              ┌─────────────────┐
              │ Eye State Manager│
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Emotion      Animation     Timing
          │            │            │
          └────────────┼────────────┘
                       ↓
                  Eye Renderer
                       ↓
                  Laptop Screen
```

The vision system should NOT directly control eye animations.

For example:

```text
Vision:
"Rice and Egg detected"

        ↓

Pet Logic:
"Correct food"

        ↓

Pet State:
HAPPY

        ↓

Eye Animation:
HAPPY animation
```

This keeps the architecture modular.

---

# 6. Initial Eye States

Implement at least these eye expressions:

```text
IDLE
HAPPY
HUNGRY
SAD
LONELY
SURPRISED
SLEEPY
CONFUSED
```

Each state should have a distinct visual expression.

---

# 7. IDLE Eyes

Default state.

Example:

```text
●       ●
```

The eyes should:

- remain relaxed
- blink periodically
- occasionally look slightly left/right
- have subtle movement

Do not make the animation too active.

The pet should feel alive even when the user does nothing.

---

# 8. Natural Blinking

Implement automatic blinking.

Example sequence:

```text
OPEN
 ↓
HALF CLOSED
 ↓
CLOSED
 ↓
HALF OPEN
 ↓
OPEN
```

Blink duration should be short.

Blink intervals should have some randomness.

Do NOT blink at an exact fixed interval such as:

```text
every 3 seconds exactly
```

Instead use randomized timing within a configurable range.

Example:

```python
BLINK_MIN_INTERVAL = 2.5
BLINK_MAX_INTERVAL = 6.0
```

This makes the pet feel more alive.

---

# 9. HAPPY Eyes

When the pet receives the correct food:

```text
Requested:
Rice and Egg

Detected:
Rice and Egg

        ↓

Correct!

        ↓

HAPPY
```

The eyes should visually communicate happiness.

Possible animation:

```text
^       ^
```

or:

```text
◕       ◕
```

Animation:

```text
normal
  ↓
eyes become happy
  ↓
small bounce / sparkle
  ↓
return to idle
```

Then play the English voice response:

> "Yay! That's exactly what I wanted! Thank you!"

The eye animation should happen at approximately the same time as the voice response.

---

# 10. HUNGRY Eyes

When the pet is hungry:

```text
╭╮     ╭╮
```

The eyes should appear slightly tired or pleading.

Possible animation:

- slow blinking
- slightly lowered eyelids
- subtle downward movement

The pet may say:

> "My tummy is getting hungry..."

---

# 11. SAD Eyes

When happiness becomes low:

```text
╲       ╱
```

or another simple sad expression.

Animation:

- slower movement
- slower blinking
- slightly lowered eyes

Voice:

> "I'm feeling a little sad..."

Keep all emotional feedback child-friendly.

---

# 12. LONELY Eyes

When the pet has not received interaction for a long time:

```text
·       ·
```

The eyes should look less energetic.

Possible behavior:

- look toward the edge of the screen
- slow blink
- occasionally look around as if searching for the user

Voice:

> "I miss playing with you."

Do not make the pet guilt-trip or emotionally manipulate the child.

---

# 13. SURPRISED Eyes

When unexpected food is detected or a new interaction occurs:

```text
●       ●
```

Make the pupils slightly larger.

Animation:

```text
NORMAL
   ↓
SURPRISED
   ↓
NORMAL
```

Example voice:

> "Oh! What's that?"

---

# 14. CONFUSED Eyes

When the system detects a food that does not match the requested food:

```text
?       ?
```

The eyes can:

- look left
- look right
- blink
- return to normal

Example voice:

> "Hmm... that's not what I asked for. Can you try again?"

---

# 15. SLEEPY Eyes

When energy is low:

```text
—       —
```

Animation:

- slow blinking
- eyelids partially closed
- subtle downward movement

Voice:

> "I'm getting sleepy..."

---

# 16. Event-Based Eye Animations

In addition to persistent states, support temporary animations.

Examples:

```text
FOOD_DETECTED
CORRECT_FOOD
WRONG_FOOD
STARTUP
ERROR
```

These are events rather than permanent states.

Example:

```text
IDLE
 ↓
FOOD_DETECTED
 ↓
SURPRISED animation
 ↓
CORRECT_FOOD
 ↓
HAPPY animation
 ↓
IDLE
```

This distinction is important.

Do not treat every animation as a permanent pet state.

---

# 17. Eye Animation Priority

Implement animation priority to prevent conflicting animations.

Suggested priority:

```text
CORRECT_FOOD
    ↓
WRONG_FOOD
    ↓
FOOD_DETECTED
    ↓
SLEEPY / SAD / LONELY / HUNGRY
    ↓
IDLE
```

Temporary event animations should override normal idle animations.

After the temporary animation finishes, the pet should return to its current persistent state.

Example:

```text
Persistent State:
HUNGRY

User shows correct food

        ↓

Temporary:
HAPPY animation

        ↓

Animation ends

        ↓

Persistent State:
HAPPY
```

---

# 18. Eye Renderer

Create an independent renderer.

Suggested architecture:

```python
class EyeRenderer:
    def set_state(self, state):
        ...

    def trigger_event(self, event):
        ...

    def update(self, delta_time):
        ...

    def render(self, surface):
        ...
```

The renderer should not know anything about:

- YOLO
- food classes
- camera
- TTS
- database

It should only receive:

```text
state
event
time
```

and render the appropriate animation.

---

# 19. Pet Engine Integration

The pet engine should control the eye state.

Example:

```python
pet.set_state(PetState.HUNGRY)
eyes.set_state(EyeState.HUNGRY)
```

Correct food:

```python
pet.handle_correct_food()

eyes.trigger_event(EyeEvent.CORRECT_FOOD)

tts.speak(
    "Yay! That's exactly what I wanted! Thank you!"
)
```

The eye system should remain independent from TTS.

---

# 20. Visual Layout

The laptop application should have two primary areas:

```text
┌───────────────────────────────────────────────┐
│                                               │
│                VIRTUAL PET                    │
│                                               │
│              ●●       ●●                      │
│                                               │
│                 ╭────╮                        │
│                                               │
│        "I'm feeling hungry..."                │
│                                               │
├───────────────────────┬───────────────────────┤
│ CAMERA                │ PET STATUS            │
│                       │                       │
│ [Webcam Preview]      │ Mood: Hungry          │
│                       │ Hunger: 72%            │
│                       │ Happiness: 65%         │
│                       │                       │
│ Detected:             │ Wants:                 │
│ Rice and Egg          │ Rice and Egg           │
│ Confidence: 94%      │                       │
└───────────────────────┴───────────────────────┘
```

The pet face should be the visual centerpiece.

The camera preview and debug information should be secondary.

---

# 21. Animation Performance

The animation should feel smooth.

Target:

```text
~30 FPS minimum
```

Prefer:

```text
60 FPS
```

if the laptop can handle it.

Vision inference does NOT need to run at the same frame rate as the eye renderer.

For example:

```text
Eye Renderer:
60 FPS

Camera:
30 FPS

YOLO:
5–15 FPS
```

This separation is important for smooth animation.

The eyes should remain smooth even when the vision model is processing.

---

# 22. Avoid Blocking the UI

Do not allow:

```text
YOLO inference
TTS generation
camera capture
```

to block the animation loop.

Use appropriate background threads, queues, or asynchronous processing where necessary.

The eye animation must continue running smoothly while:

- YOLO is processing
- TTS is playing
- camera frames are being processed

---

# 23. Future Hardware Compatibility

The eye system must be designed so that the current laptop renderer can later be replaced.

Current:

```text
Pet Engine
    ↓
EyeRenderer
    ↓
Laptop Screen
```

Future:

```text
Pet Engine
    ↓
EyeRenderer
    ↓
Physical Display
```

Possible future display:

- OLED
- TFT LCD
- LED matrix
- small HDMI display

The pet logic should not need to change when the display hardware changes.

---

# 24. Suggested Project Structure

Add the eye system to the previous project structure:

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
│   ├── eyes/
│   │   ├── renderer.py
│   │   ├── states.py
│   │   ├── animations.py
│   │   └── events.py
│   │
│   ├── audio/
│   │   └── tts.py
│   │
│   └── ui/
│       └── dashboard.py
│
├── data/
├── models/
├── scripts/
├── logs/
├── requirements.txt
└── README.md
```

---

# 25. Initial Animation Requirements

For the first implementation, prioritize these animations:

### 1. Idle

Natural blinking + subtle eye movement.

### 2. Happy

Triggered after correct food.

### 3. Hungry

Triggered when the pet needs food.

### 4. Sad

Triggered when happiness decreases.

### 5. Confused

Triggered after incorrect food.

### 6. Surprised

Triggered when a new food is detected.

### 7. Sleepy

Triggered when energy is low.

Do not spend excessive time creating dozens of animations.

A small number of polished animations is better.

---

# 26. Interaction Example

The complete interaction should eventually look like this:

```text
PET:

Eyes:
Idle animation

Voice:
"I'm feeling hungry.
I think I'd like some rice and egg."

                ↓

USER:

Shows Rice & Egg card
from smartphone

                ↓

CAMERA:

Detects:
Rice and Egg

Confidence:
94%

                ↓

PET ENGINE:

Requested:
Rice and Egg

Detected:
Rice and Egg

Result:
CORRECT

                ↓

EYES:

SURPRISED
      ↓
HAPPY
      ↓
small happy animation

                ↓

VOICE:

"Yay! That's exactly what I wanted!
Thank you!"

                ↓

PET STATE:

HUNGRY → HAPPY
```

---

# 27. Startup Animation

When the application starts, play a short startup animation.

Example:

```text
Eyes closed
    ↓
Eyes slowly open
    ↓
Blink
    ↓
Happy / Idle
```

Voice:

> "Hi! I'm ready to play!"

Keep the startup animation short.

---

# 28. Important Implementation Rules

1. The eye system must be modular.
2. The eye renderer must not depend directly on YOLO.
3. The eye renderer must not depend directly on TTS.
4. Persistent pet states and temporary eye events must be separated.
5. Animations must not block the main UI.
6. Vision inference must not freeze the animation.
7. TTS must not freeze the animation.
8. Animation parameters should be configurable.
9. Keep the initial visual design simple.
10. Prioritize smoothness and expressiveness over graphical complexity.

---

# 29. Definition of Done — Eye System

This feature is complete when:

- [ ] Animated pet eyes appear on the laptop screen.
- [ ] Eyes have a clear idle animation.
- [ ] Eyes blink naturally.
- [ ] Eyes have at least 7 distinct expressions/states.
- [ ] Correct food triggers a happy eye animation.
- [ ] Incorrect food triggers a confused/sad animation.
- [ ] Food detection triggers a visual response.
- [ ] Pet hunger affects eye expression.
- [ ] Temporary eye events override persistent states correctly.
- [ ] Eyes return to the correct persistent state after temporary animations.
- [ ] Animation remains smooth while YOLO is running.
- [ ] Animation remains smooth while TTS is playing.
- [ ] Eye renderer is modular and independent from vision logic.
- [ ] Eye system can later be replaced by a physical display renderer.

---

# 30. Development Priority

Implement the eye system in this order:

### Step 1
Create the basic pet face window.

### Step 2
Implement two eyes with simple vector/drawn shapes.

### Step 3
Add idle animation.

### Step 4
Add natural blinking.

### Step 5
Add state-based expressions.

### Step 6
Add temporary event animations.

### Step 7
Connect eye state to Pet Engine.

### Step 8
Connect correct/wrong food events.

### Step 9
Connect eye animations with English TTS responses.

### Step 10
Test performance while webcam + YOLO + TTS are running simultaneously.

Do not redesign the entire application architecture just to add the eye system.

Integrate it into the existing modular architecture.