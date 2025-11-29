from .embeddings import query_index
from .llm import chat_llm

RAG_SYSTEM_PROMPT = """
You are a helpful school tutor. Answer using simple words.
Use ONLY the provided context from the textbook.
If you don't know, say you are not sure.
"""

def answer_question(episode_id: str, question: str, timestamp: float | None):
    context_docs = query_index(episode_id, question, top_k=5)
    context = "\n\n---\n\n".join(context_docs)

    user_prompt = f"""
CONTEXT:
{context}

QUESTION: {question}

Answer clearly in 3-6 sentences.
"""

    answer = chat_llm(RAG_SYSTEM_PROMPT, user_prompt)
    return answer, context_docs
# RAG pipeline