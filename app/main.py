"""
Main Application Entry Point.
Coordinates Vision, Pet State Engine, 60 FPS Eye Animation, Audio TTS, and UI Dashboard.
Integrated with Child-Like Pet Voice and EmotionOrchestrator.
"""
import logging
import sys
import time
import pygame

from .config import config, CATALOG_PATH
from .pet.state import PetState, PetMood
from .pet.food_request import FoodRequestManager
from .pet.behavior import PetBehaviorEngine, BehaviorOutcome
from .pet.orchestrator import EmotionOrchestrator
from .eyes.renderer import EyeRenderer
from .eyes.states import EyeState
from .eyes.events import EyeEvent
from .vision.camera import CameraManager
from .vision.detector import FoodDetector
from .vision.stabilizer import TemporalStabilizer
from .sensors.touch import TouchSensor, TouchSensorError
from .audio.tts import create_tts_service
from .audio.profiles import PetEmotion
from .ui.dashboard import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pet.main")


def run():
    logger.info("Initializing Interactive AI Pet Prototype...")

    # 1. Initialize Pet State and Food Manager
    food_manager = FoodRequestManager(CATALOG_PATH)
    pet_state = PetState(
        initial_mood=PetMood.HUNGRY,
        hunger=config.initial_hunger,
        happiness=config.initial_happiness,
        energy=config.initial_energy,
    )
    behavior_engine = PetBehaviorEngine(
        pet_state=pet_state,
        food_manager=food_manager,
        cooldown_seconds=config.response_cooldown_seconds,
    )

    # 2. Initialize Eye Animation Renderer (60 FPS)
    eye_renderer = EyeRenderer(
        blink_min_interval=config.blink_min_interval,
        blink_max_interval=config.blink_max_interval,
    )

    # 3. Initialize Vision Pipeline (Webcam + YOLO/ORB + Stabilizer)
    camera = CameraManager(
        camera_index=config.camera_index,
        width=config.camera_width,
        height=config.camera_height,
    )
    camera.start()

    food_catalog_dict = {f.id: f.name for f in food_manager.get_all_foods()}
    detector = FoodDetector(
        model_path=config.model_path,
        catalog_foods=food_catalog_dict,
        confidence_threshold=config.confidence_threshold,
        enable_async=True,
    )
    detector.start()

    stabilizer = TemporalStabilizer(
        required_consecutive_frames=config.required_consecutive_frames,
        confidence_threshold=config.confidence_threshold,
    )

    # 4. Initialize Child-Like TTS Voice Service
    tts = create_tts_service(
        enabled=config.enable_tts,
        provider_name=config.voice_provider,
    )

    # 5. Initialize UI Dashboard
    dashboard = Dashboard(
        width=config.window_width,
        height=config.window_height,
        title="Interactive AI Pet Food Vision Prototype",
    )

    # 6. Initialize Shared Emotion Orchestrator (Synchronizes Eyes + Voice with 0.1s delay)
    orchestrator = EmotionOrchestrator(
        eye_renderer=eye_renderer,
        tts_service=tts,
        voice_start_delay=config.voice_start_delay,
    )

    touch_sensor = None
    if config.touch_sensor_enabled:
        touch_sensor = TouchSensor(port=config.touch_sensor_port)

    def handle_affection(source: str) -> None:
        pet_state.give_affection(20.0)
        pat_intent = behavior_engine.get_pat_intent()
        orchestrator.emit_emotion(
            emotion=pat_intent.emotion,
            message=pat_intent.text,
            eye_event=EyeEvent.CORRECT_FOOD,
            dashboard=dashboard,
            speech_duration=3.0,
        )
        dashboard.log_event(source)

    # 7. Startup Sequence (PRD Addendum Section 27)
    dashboard.log_event("Application initialized")
    dashboard.log_event("Camera capture started")

    startup_intent = behavior_engine.get_startup_intent()
    orchestrator.emit_emotion(
        emotion=startup_intent.emotion,
        message=startup_intent.text,
        eye_event=EyeEvent.STARTUP,
        dashboard=dashboard,
        speech_duration=3.5,
    )
    # Schedule pet to autonomously announce what food it wants 3.8s after waking up
    behavior_engine.schedule_initial_desire_announcement(delay=3.8)

    # Food index mapping for keyboard simulation: 1-5
    food_list = food_manager.get_all_foods()
    key_food_map = {
        pygame.K_1: food_list[0].id if len(food_list) > 0 else None,
        pygame.K_2: food_list[1].id if len(food_list) > 1 else None,
        pygame.K_3: food_list[2].id if len(food_list) > 2 else None,
        pygame.K_4: food_list[3].id if len(food_list) > 3 else None,
        pygame.K_5: food_list[4].id if len(food_list) > 4 else None,
    }

    last_time = time.perf_counter()
    running = True

    try:
        if touch_sensor:
            try:
                touch_sensor.start()
                dashboard.log_event(
                    f"Touch sensor connected on {config.touch_sensor_port}"
                )
            except TouchSensorError as exc:
                logger.error("%s", exc)
                dashboard.log_event(f"Touch sensor unavailable: {exc}")

        while running:
            # High-precision delta time
            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time
            dt = min(dt, 0.1)  # Clamp frame spike

            # ------------------------------------------------------------------
            # Event Handling & Hotkeys
            # ------------------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if dashboard.rect_pet.collidepoint(event.pos):
                        handle_affection("User stroked pet (+20% Happiness)")
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key in key_food_map and key_food_map[event.key]:
                        # Simulate card presentation
                        f_id = key_food_map[event.key]
                        detector.simulate_detection(f_id, duration=2.5)
                        dashboard.log_event(f"Simulating food card: {f_id}")
                    elif event.key == pygame.K_r:
                        # Change food request & trigger hunger dialogue
                        new_req = food_manager.select_random_request(exclude_current=True)
                        dashboard.log_event(f"New pet desire: {new_req.name}")
                        reminder_intent = behavior_engine.get_hunger_reminder_intent()
                        if reminder_intent:
                            orchestrator.emit_emotion(
                                emotion=reminder_intent.emotion,
                                message=reminder_intent.text,
                                dashboard=dashboard,
                                speech_duration=4.0,
                            )
                    elif event.key == pygame.K_p:
                        handle_affection("User gave affection (+20% Happiness)")

            if touch_sensor and touch_sensor.poll_touch():
                handle_affection("User touched pet (+20% Happiness)")

            # ------------------------------------------------------------------
            # Vision & Detection Processing
            # ------------------------------------------------------------------
            has_frame, frame = camera.get_frame()
            if has_frame and frame is not None:
                detector.submit_frame(frame)

            raw_det = detector.get_latest_result()
            stab_det = stabilizer.update(
                detected_id=raw_det.food_id,
                confidence=raw_det.confidence,
                box=raw_det.box,
            )

            # Trigger SURPRISED eye animation when new food is first spotted
            if stab_det.consecutive_count == 1 and stab_det.food_id:
                eye_renderer.trigger_event(EyeEvent.FOOD_DETECTED)
                dashboard.log_event(f"Food detected: {stab_det.food_id} ({int(stab_det.confidence * 100)}%)")

            # ------------------------------------------------------------------
            # Pet Interaction & Confirmation Evaluation
            # ------------------------------------------------------------------
            if stab_det.is_confirmed and stab_det.food_id:
                event_result = behavior_engine.handle_confirmed_food(stab_det.food_id)

                if event_result.outcome == BehaviorOutcome.CORRECT:
                    dashboard.log_event(f"Confirmed: CORRECT ({event_result.detected_food})")
                    if event_result.speech_text:
                        orchestrator.emit_emotion(
                            emotion=event_result.emotion,
                            message=event_result.speech_text,
                            eye_event=EyeEvent.CORRECT_FOOD,
                            dashboard=dashboard,
                            speech_duration=4.5,
                        )
                    stabilizer.reset()

                elif event_result.outcome == BehaviorOutcome.WRONG:
                    dashboard.log_event(f"Confirmed: WRONG ({event_result.detected_food})")
                    if event_result.speech_text:
                        orchestrator.emit_emotion(
                            emotion=event_result.emotion,
                            message=event_result.speech_text,
                            eye_event=EyeEvent.WRONG_FOOD,
                            dashboard=dashboard,
                            speech_duration=4.5,
                        )
                    stabilizer.reset()

            # ------------------------------------------------------------------
            # State Synchronization & Passive Updates
            # ------------------------------------------------------------------
            pet_state.update_passive(dt)
            dashboard.update_timers(dt)

            # Map PetMood to EyeState
            mood_map = {
                PetMood.HAPPY: EyeState.HAPPY,
                PetMood.HUNGRY: EyeState.HUNGRY,
                PetMood.SAD: EyeState.SAD,
                PetMood.LONELY: EyeState.LONELY,
                PetMood.SLEEPY: EyeState.SLEEPY,
            }
            eye_renderer.set_persistent_state(mood_map.get(pet_state.mood, EyeState.IDLE))
            eye_renderer.update(dt)

            # ------------------------------------------------------------------
            # Autonomous Spontaneous Vocalization (Speaks without user input)
            # ------------------------------------------------------------------
            if not tts.is_speaking():
                auto_intent = behavior_engine.check_autonomous_vocalization(time.time())
                if auto_intent:
                    orchestrator.emit_emotion(
                        emotion=auto_intent.emotion,
                        message=auto_intent.text,
                        dashboard=dashboard,
                        speech_duration=4.0,
                    )


            # ------------------------------------------------------------------
            # Render Unified 60 FPS Dashboard
            # ------------------------------------------------------------------
            fps = dashboard.clock.get_fps()
            dashboard.render(
                eye_renderer=eye_renderer,
                pet_state=pet_state,
                current_request=food_manager.current_request,
                camera_frame_bgr=frame,
                stabilized_detection=stab_det,
                fps=fps,
            )

            # Regulate to 60 FPS
            dashboard.clock.tick(config.fps)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info("Cleaning up and stopping subsystems...")
        if touch_sensor:
            touch_sensor.stop()
        camera.stop()
        detector.stop()
        tts.stop()
        pygame.quit()
        logger.info("Prototype closed cleanly.")


if __name__ == "__main__":
    run()
