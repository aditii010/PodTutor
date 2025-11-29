from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.Client()
COLLECTION_PREFIX = "episode_"

def build_index(episode_id: str, chunks: list[str]):
    coll = client.create_collection(COLLECTION_PREFIX + episode_id)
    vectors = model.encode(chunks).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    coll.add(ids=ids, embeddings=vectors, documents=chunks)

def query_index(episode_id: str, query: str, top_k: int = 4):
    coll = client.get_collection(COLLECTION_PREFIX + episode_id)
    q_emb = model.encode([query]).tolist()
    res = coll.query(query_embeddings=q_emb, n_results=top_k)
    return res["documents"][0]
# Embedding generation