from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from uuid import uuid4
import os
import json
import threading

from core.services import pdf_parser, chunker, embeddings, script_gen, tts, rag

router = APIRouter()

BASE_STORAGE = "storage"
EPISODE_DIR = os.path.join(BASE_STORAGE, "episodes")


# ==============================
# ✅ BACKGROUND PIPELINE
# ==============================
def process_episode_pipeline(episode_id: str, pdf_path: str):
    episode_path = os.path.join(EPISODE_DIR, episode_id)
    manifest_path = os.path.join(episode_path, "manifest.json")

    # ✅ CACHE CHECK
    if os.path.exists(manifest_path):
        return

    # 1. EXTRACT TEXT
    full_text = pdf_parser.extract_text(pdf_path)

    # 2. CHUNK
    chunks = chunker.chunk_text(full_text)

    # 3. BUILD VECTOR INDEX (FAST)
    embeddings.build_index(episode_id, chunks)

    # 4. PARALLEL SCRIPT GENERATION
    script_segments = script_gen.generate_script_parallel(chunks)

    # 5. PARALLEL TTS GENERATION
    audio_results = tts.generate_tts_parallel(
        episode_id, script_segments
    )

    # 6. BUILD MANIFEST WITH TIMING
    manifest = []
    current_time = 0.0

    for seg in audio_results:
        seg["start"] = current_time
        current_time += seg["duration"]
        seg["end"] = current_time
        manifest.append(seg)

    # 7. SAVE MANIFEST
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)


# ==============================
# ✅ UPLOAD (NON-BLOCKING)
# ==============================
@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    episode_id = str(uuid4())
    episode_path = os.path.join(EPISODE_DIR, episode_id)
    os.makedirs(episode_path, exist_ok=True)

    pdf_path = os.path.join(episode_path, "source.pdf")
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # ✅ START BACKGROUND THREAD
    threading.Thread(
        target=process_episode_pipeline,
        args=(episode_id, pdf_path),
        daemon=True
    ).start()

    return {
        "episode_id": episode_id,
        "status": "processing"
    }


# ==============================
# ✅ STATUS POLLING
# ==============================
@router.get("/{episode_id}/status")
async def get_status(episode_id: str):
    manifest_path = os.path.join(
        EPISODE_DIR, episode_id, "manifest.json"
    )

    if os.path.exists(manifest_path):
        return {"status": "ready"}

    return {"status": "processing"}


# ==============================
# ✅ MANIFEST FETCH
# ==============================
@router.get("/{episode_id}/manifest")
async def get_manifest(episode_id: str):
    episode_path = os.path.join(EPISODE_DIR, episode_id)
    manifest_path = os.path.join(episode_path, "manifest.json")

    if not os.path.exists(manifest_path):
        raise HTTPException(status_code=404, detail="Manifest not ready")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    return manifest


# ==============================
# ✅ MID-PODCAST QUESTION (RAG)
# ==============================
@router.post("/{episode_id}/question")
async def ask_in_episode(episode_id: str, payload: dict = Body(...)):
    question = payload["question"]
    timestamp = float(payload["timestamp"])

    answer_text, context_chunks = rag.answer_question(
        episode_id, question, timestamp
    )

    episode_path = os.path.join(EPISODE_DIR, episode_id)
    audio_filename = f"question_{uuid4().hex}.mp3"
    audio_path = os.path.join(episode_path, audio_filename)

    tts.generate_single_audio(answer_text, audio_path)

    return {
        "answer_text": answer_text,
        "answer_audio_url": f"/static/episodes/{episode_id}/{audio_filename}",
        "context": context_chunks,
    }


# ==============================
# ✅ SIDE TUTOR CHAT
# ==============================
@router.post("/{episode_id}/chat")
async def chat_with_tutor(episode_id: str, payload: dict = Body(...)):
    message = payload["message"]

    answer_text, _ = rag.answer_question(
        episode_id, message, timestamp=None
    )

    return {"answer_text": answer_text}
