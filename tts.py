from concurrent.futures import ThreadPoolExecutor
from gtts import gTTS
import os

def generate_one_audio(item):
    episode_id, index, text = item
    audio_path = f"storage/episodes/{episode_id}/seg_{index}.mp3"

    tts = gTTS(text=text[:1200], lang="en")
    tts.save(audio_path)

    duration = max(2.0, len(text.split()) / 2.5)

    return {
        "segment_id": index,
        "speaker": "Tutor",
        "text": text,
        "audio_url": f"/static/episodes/{episode_id}/seg_{index}.mp3",
        "duration": duration,
    }


def generate_tts_parallel(episode_id, segments):
    tasks = [
        (episode_id, i, seg["text"])
        for i, seg in enumerate(segments)
    ]

    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(generate_one_audio, tasks):
            results.append(result)

    return results
