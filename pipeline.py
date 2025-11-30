import json
import os
import time
from pathlib import Path
from core.services import pdf_parser, chunker, embeddings, script_gen, tts

# Get project root (3 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / "backend" / "storage"


def process_episode_pipeline(episode_id: str, pdf_path: str):
    """
    FREE optimized pipeline - NO API KEYS NEEDED
    Target: 3-5 seconds for typical PDFs
    """
    episode_path = STORAGE_DIR / "episodes" / episode_id
    manifest_path = episode_path / "manifest.json"

    # Check cache
    if manifest_path.exists():
        print(f"✅ Using cached manifest for {episode_id}")
        return

    start_time = time.time()

    try:
        print(f"\n{'=' * 50}")
        print(f"🎙️  STARTING PODCAST GENERATION")
        print(f"{'=' * 50}\n")

        # STEP 1: Extract text from PDF
        print(f"📄 Step 1: Extracting text from PDF...")
        step_start = time.time()
        full_text = pdf_parser.extract_text(pdf_path)
        print(f"   ✓ Extracted {len(full_text)} characters")
        print(f"   ⏱️  {time.time() - step_start:.2f}s\n")

        # STEP 2: Chunk text into segments
        print(f"✂️  Step 2: Chunking text...")
        step_start = time.time()
        chunks = chunker.chunk_text(full_text, max_chars=600)

        # Limit for speed (you can adjust this)
        chunks = chunks[:8]  # Process first 8 chunks
        print(f"   ✓ Created {len(chunks)} chunks")
        print(f"   ⏱️  {time.time() - step_start:.2f}s\n")

        # STEP 3: Build embeddings in background (for RAG/search)
        print(f"🔍 Step 3: Building search index (background)...")
        embeddings.build_index_async(episode_id, chunks)
        print(f"   ✓ Index building started\n")

        # STEP 4: Generate script (template-based - INSTANT)
        print(f"✍️  Step 4: Generating dialogue script...")
        step_start = time.time()
        segments = script_gen.generate_script_parallel(chunks)
        print(f"   ✓ Generated {len(segments)} dialogue segments")
        print(f"   ⏱️  {time.time() - step_start:.2f}s\n")

        # STEP 5: Generate TTS audio (parallel with caching)
        print(f"🎙️  Step 5: Generating audio files...")
        step_start = time.time()
        audio_results = tts.generate_tts_parallel(episode_id, segments)
        print(f"   ✓ Generated {len(audio_results)} audio files")
        print(f"   ⏱️  {time.time() - step_start:.2f}s\n")

        # STEP 6: Build manifest with timing information
        print(f"📋 Step 6: Building manifest...")
        manifest = []
        current_time = 0.0

        for seg in audio_results:
            seg["start"] = current_time
            current_time += seg["duration"]
            seg["end"] = current_time
            manifest.append(seg)

        # STEP 7: Save manifest to disk
        episode_path.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        total_time = time.time() - start_time
        total_duration = sum(s["duration"] for s in manifest)

        print(f"\n{'=' * 50}")
        print(f"✅ PODCAST GENERATION COMPLETE!")
        print(f"{'=' * 50}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📊 Podcast duration: {total_duration:.1f}s")
        print(f"🎯 Efficiency: {total_duration / total_time:.1f}x realtime")
        print(f"💾 Saved to: {episode_id}")
        print(f"{'=' * 50}\n")

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        raise
