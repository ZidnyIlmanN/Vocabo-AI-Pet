"""
Pre-caches all standard pet dialogue lines using EdgeTTSChildProvider
so the application runs with 0 network latency and 100% offline-ready audio.
"""
import asyncio
import hashlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.audio.tts import EdgeTTSChildProvider
from app.audio.profiles import PetEmotion
from app.pet.behavior import PetBehaviorEngine
from app.pet.state import PetState
from app.pet.food_request import FoodRequestManager

def main():
    mgr = FoodRequestManager(ROOT_DIR / "data" / "food_catalog.json")
    state = PetState()
    engine = PetBehaviorEngine(state, mgr)
    provider = EdgeTTSChildProvider()

    # Collect all dialogue phrases
    items_to_cache = []
    items_to_cache.extend([(phrase, PetEmotion.HAPPY) for phrase in engine.correct_phrases])
    for food in mgr.get_all_foods():
        for tpl in engine.wrong_phrases:
            items_to_cache.append((tpl.format(requested_name=food.name.lower()), PetEmotion.CONFUSED))
        for tpl in engine.hunger_reminders:
            items_to_cache.append((tpl.format(requested_name=food.name.lower()), PetEmotion.HUNGRY))
        for tpl in engine.food_desire_announcements:
            items_to_cache.append((tpl.format(requested_name=food.name.lower()), PetEmotion.HUNGRY))
    items_to_cache.extend([(phrase, PetEmotion.HAPPY) for phrase in engine.startup_phrases])
    items_to_cache.extend([(phrase, PetEmotion.HAPPY) for phrase in engine.pat_phrases])
    items_to_cache.extend([(phrase, PetEmotion.SLEEPY) for phrase in engine.sleepy_phrases])
    items_to_cache.extend([(phrase, PetEmotion.LONELY) for phrase in engine.lonely_phrases])

    # Also cache the 10 PRD test sentences
    from scripts.test_voice import REQUIRED_TEST_SENTENCES
    for emo, text in REQUIRED_TEST_SENTENCES:
        items_to_cache.append((text, emo))

    print(f"Pre-caching {len(items_to_cache)} child voice audio files...")

    async def cache_all():
        import edge_tts
        count = 0
        for text, emo in items_to_cache:
            tuning = provider.EMOTION_TUNING.get(emo, {"rate": "+0%", "pitch": "+0Hz"})
            rate_val = tuning["rate"]
            pitch_val = tuning["pitch"]
            key_str = f"{provider.voice}_{emo.value}_{rate_val}_{pitch_val}_{text}"
            cache_key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
            audio_file = provider.cache_dir / f"{cache_key}.mp3"
            if not audio_file.exists() or audio_file.stat().st_size == 0:
                try:
                    comm = edge_tts.Communicate(text, provider.voice, rate=rate_val, pitch=pitch_val)
                    await comm.save(str(audio_file))
                    count += 1
                    print(f"[{count}] Cached: [{emo.value}] {text[:38]}...")
                except Exception as e:
                    print(f"Failed to cache '{text[:30]}': {e}")
            else:
                pass
        print(f"Done! {count} new audio files generated. Total in cache: {len(list(provider.cache_dir.glob('*.mp3')))}")

    asyncio.run(cache_all())

if __name__ == "__main__":
    main()
