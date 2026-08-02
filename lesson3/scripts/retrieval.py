
from __future__ import annotations

import sys
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer
import chunk

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNKS_PATH = Path("/Users/andrew/rag/lesson3/data/processed/chunks.jsonl")
FAISS_INDEX_PATH = Path("/Users/andrew/rag/lesson3/index/faiss.index")
TOP_K = 3


def search(query: str, index: faiss.Index, model: SentenceTransformer, chunks: list[dict], top_k: int = TOP_K) -> list[dict]:
    query_vector = model.encode([query], convert_to_numpy=True).astype("float32")
    distances, positions = index.search(query_vector, top_k)

    results = []
    for distance, position in zip(distances[0], positions[0]):
        chunk_record = chunks[position]
        results.append(
            {
                "distance": float(distance),
                "chunk_id": chunk_record["chunk_id"],
                "text": chunk_record["text"],
                "metadata": chunk_record["metadata"],
            }
        )
    return results


def main() -> None:
    query = " ".join(sys.argv[1:])
    chunks = chunk.load_jsonl(CHUNKS_PATH)
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    model = SentenceTransformer(MODEL_NAME)

    results = search(query, index, model, chunks)

    print(f"Query: {query}")
    print("=" * 80)
    for rank, result in enumerate(results, start=1):
        preview = result["text"][:220].replace("\n", " ")
        print(f"#{rank} | distance={result['distance']:.4f} | {result['chunk_id']}")
        print(f"  {preview}...")
        print("-" * 80)


if __name__ == "__main__":
    main()
