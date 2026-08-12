from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import hybrid_search_retrieval

DEFAULT_MODEL = "gpt-4.1-mini"

USER_QUESTION = "what is middleware?"


def format_retrieved_context(retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return "No retrieved context."

    context_blocks = []
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        metadata = chunk.get("metadata", {})
        context_blocks.append(
            "\n".join(
                [
                    f"Result rank: {rank}",
                    f"Source chunk ID: {chunk.get('chunk_id', 'unknown')}",
                    f"Retrieval score: {chunk.get('score', 'unknown')}",
                    f"Title: {metadata.get('title', 'unknown')}",
                    f"Source file: {metadata.get('source_file', 'unknown')}",
                    "Content:",
                    chunk.get("text", ""),
                ]
            )
        )

    return "\n---\n".join(context_blocks)


def build_weak_prompt(user_question: str, retrieved_context: str) -> str:
    return f"""
Answer the user question using the context.

Context:
{retrieved_context}

Question:
{user_question}
""".strip()


def build_grounded_rag_prompt(user_question: str, retrieved_context: str) -> str:
    return f"""
You are a documentation assistant for Gin framework users.
Your task:
Answer the user question using only the retrieved context.
Rules:
- Do not use external knowledge.
- Do not invent missing information.
- If the retrieved context does not contain enough information, say:
  "I do not have enough information in the provided context."
- Cite every factual claim with the source chunk ID, for example (doc_chunk_015).
- Prefer the highest-ranked relevant chunks when multiple chunks overlap.
- Keep the answer concise and practical.
Retrieved context:
{retrieved_context}
User question:
{user_question}
Answer:
""".strip()


def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Create a .env file or export OPENAI_API_KEY before running this script."
        )


def call_responses_api(client: OpenAI, model: str, prompt: str) -> str:
    response = client.responses.create(model=model, input=prompt)
    return response.output_text


def format_source_file(source_file: str) -> str:
    if not source_file:
        return "unknown"

    source_path = Path(source_file)
    try:
        return str(source_path.relative_to(Path.cwd()))
    except ValueError:
        return str(source_path)


def format_final_report(user_question: str, retrieved_chunks: list[dict], answer: str) -> str:
    retrieved_chunk_ids = []
    source_files = []

    for chunk in retrieved_chunks:
        retrieved_chunk_ids.append(chunk.get("chunk_id", "unknown"))

        source_file = chunk.get("metadata", {}).get("source_file")
        if source_file:
            source_files.append(format_source_file(source_file))

    retrieved_block = ", ".join(retrieved_chunk_ids) if retrieved_chunk_ids else "none"
    unique_source_files = list(dict.fromkeys(source_files))
    source_block = ", ".join(unique_source_files) if unique_source_files else "unknown"

    return f"""
Question: {user_question}

Retrieved chunks: {retrieved_block}

Answer:
{answer.strip()}

Source: {source_block}

""".strip()


def main() -> None:

    retrieval_results = hybrid_search_retrieval.retrieval(USER_QUESTION)

    retrieved_context = format_retrieved_context(retrieval_results)
    weak_prompt = build_weak_prompt(USER_QUESTION, retrieved_context)
    grounded_rag_prompt = build_grounded_rag_prompt(USER_QUESTION, retrieved_context)

    load_dotenv()
    require_api_key()
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    client = OpenAI()

    weak_answer = call_responses_api(client, model, weak_prompt)
    grounded_answer = call_responses_api(client, model, grounded_rag_prompt)

    print("WEAK PROMPT RESULT")
    print(format_final_report(USER_QUESTION, retrieval_results, weak_answer))
    print()
    print("GROUNDED PROMPT RESULT")
    print(format_final_report(USER_QUESTION, retrieval_results, grounded_answer))


if __name__ == "__main__":
    main()
