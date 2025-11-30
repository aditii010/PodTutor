from gtts import gTTS
from pathlib import Path
import os
import time

PROJECT_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / "backend" / "storage"
EPISODES_DIR = STORAGE_DIR / "episodes"

# Voice settings - using speed to differentiate
VOICE_SETTINGS = {
    "Tutor": {"slow": False, "lang": "en"},
    "Student": {"slow": False, "lang": "en-us"}  # Different accent
}


def generate_one_audio(item):
    """Generate audio with basic differentiation"""
    episode_id, index, segment = item

    try:
        text = segment["text"][:800]
        speaker = segment.get("speaker", "Tutor")

        episode_dir = EPISODES_DIR / episode_id
        episode_dir.mkdir(parents=True, exist_ok=True)

        audio_filename = f"seg_{index}.mp3"
        audio_path = episode_dir / audio_filename

        # Add natural pauses to text
        if index > 0:
            prev_speaker = segment.get("prev_speaker")
            if prev_speaker and prev_speaker != speaker:
                text = "..." + text  # Add pause

        # Generate with gTTS
        settings = VOICE_SETTINGS.get(speaker, VOICE_SETTINGS["Tutor"])
        tts = gTTS(text=text, lang=settings["lang"], slow=settings["slow"])
        tts.save(str(audio_path))

        print(f"  ✓ {speaker}: {audio_filename}")

        word_count = len(text.split())
        duration = max(2.0, word_count / 2.5)

        return {
            "segment_id": index,
            "speaker": speaker,
            "text": text,
            "audio_url": f"/static/episodes/{episode_id}/{audio_filename}",
            "duration": duration,
        }

    except Exception as e:
        print(f"❌ Error {index}: {e}")
        return None


def generate_tts_parallel(episode_id, segments):
    """Generate TTS sequentially"""
    results = []
    prev_speaker = None

    print(f"\n🎙️ Generating {len(segments)} audio files...")

    for i, seg in enumerate(segments):
        seg["prev_speaker"] = prev_speaker
        result = generate_one_audio((episode_id, i, seg))
        if result:
            results.append(result)
            prev_speaker = seg.get("speaker")

    print(f"✅ Done: {len(results)} files\n")
    return results


def generate_single_audio(text: str, audio_path: str):
    """Generate answer audio"""
    try:
        tts = gTTS(text=text[:800], lang="en", slow=False)
        tts.save(audio_path)
    except Exception as e:
        print(f"❌ Answer error: {e}")
