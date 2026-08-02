
from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import chunk

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNKS_PATH = Path("/Users/andrew/rag/lesson3/data/processed/chunks.jsonl")
EMBEDDINGS_PATH = Path("/Users/andrew/rag/lesson3/data/processed/embeddings.npy")
FAISS_INDEX_PATH = Path("/Users/andrew/rag/lesson3/index/faiss.index")


def cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:

    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def euclidean_distance(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    return float(np.linalg.norm(vector_a - vector_b))


def main() -> None:
    chunks = chunk.load_jsonl(CHUNKS_PATH)
    texts = [record["text"] for record in chunks]

    model = SentenceTransformer(MODEL_NAME)

    print("Creating embeddings...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    print(f"Raw embeddings shape: {embeddings.shape}")

    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"Saved embeddings to: {EMBEDDINGS_PATH}")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype("float32"))
    print(f"FAISS index size: {index.ntotal}")

    FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    print(f"Saved FAISS index to: {FAISS_INDEX_PATH}")






if __name__ == "__main__":
    main()