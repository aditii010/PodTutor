from concurrent.futures import ThreadPoolExecutor
from .llm import chat_llm

SYSTEM_PROMPT = """
You are a school tutor. Convert the content into a short dialogue.
"""

def generate_one(chunk: str):
    user_prompt = f"""
Convert this into a short Tutor-Student dialogue (6–8 turns):

{chunk}
"""
    text = chat_llm(SYSTEM_PROMPT, user_prompt)

    segments = []
    for line in text.splitlines():
        if ":" in line:
            speaker, content = line.split(":", 1)
            segments.append({
                "speaker": speaker.strip(),
                "text": content.strip()
            })
    return segments


def generate_script_parallel(chunks):
    segments = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = pool.map(generate_one, chunks)

    for block in results:
        segments.extend(block)

    return segments
