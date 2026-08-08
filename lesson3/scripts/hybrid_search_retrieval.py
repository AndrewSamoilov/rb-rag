from rank_bm25 import BM25Okapi
import chunk as ch
from pathlib import Path
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("/Users/andrew/rag/lesson3/data/processed/chunks.jsonl")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_INDEX_PATH = Path("/Users/andrew/rag/lesson3/index/faiss.index")
TOP_K = 5


def main() -> None:
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    model = SentenceTransformer(MODEL_NAME)
    chunks = ch.load_jsonl(CHUNKS_PATH)

    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    query = "How do I skip logging?"
    query_tokens = query.split()

    splited_chuk_text = []

    for chunk in chunks:
        splited_chuk_text.append(chunk["text"].split())

    bm25 = BM25Okapi(splited_chuk_text)

    scores = bm25.get_scores(query_tokens)

    top_positions = np.argsort(scores)[::-1][:20]

    result = search(query, index, model, chunks)

    result.sort(key=lambda x: x["distance"], reverse=False)

    faiss_chunk_ids = []
    for r in result:
        faiss_chunk_ids.append(r["chunk_id"])

    bm25_chunk_ids = []
    for pos in top_positions:
        bm25_chunk_ids.append(chunks[pos]["chunk_id"])


    rank = calc_rank(bm25_chunk_ids, faiss_chunk_ids)

    sorted_rank = dict(sorted(rank.items(), key=lambda item: item[1], reverse=True))

    result = []
    for i, (cid, score) in enumerate(sorted_rank.items()):
        if i >= TOP_K:
            break

        chunk_obj = chunks_by_id.get(cid)
        if chunk_obj:
            enriched_chunk = {**chunk_obj, "score": round(score, 5)}
            result.append(enriched_chunk)

    print(result)




def calc_rank(bm25_chuck_ids, faiss_chunk_ids) -> dict:
    rrf = {}
    k = 60
    for rank, cid in enumerate(faiss_chunk_ids, start=1):
        rrf[cid] = rrf.get(cid, 0) + 1 / (k + rank)

    for rank, cid in enumerate(bm25_chuck_ids, start=1):
        rrf[cid] = rrf.get(cid, 0) + 1 / (k + rank)

    return rrf


def search(query: str, index: faiss.Index, model: SentenceTransformer, chunks: list[dict], top_k: int = TOP_K) -> list[
    dict]:
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


if __name__ == "__main__":
    main()
