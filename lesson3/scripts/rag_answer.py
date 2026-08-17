from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import external_tool
import hybrid_search_retrieval

DEFAULT_MODEL = "gpt-4.1-mini"

USER_QUESTION = "how many issues are open on github?"

GIN_RELEASE_TOOL = {
    "type": "function",
    "name": "get_gin_release_info",
    "description": "Get the latest Gin framework release from the official GitHub releases API. Use this only for current/latest Gin version, release date, release URL, or changelog questions.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

GIN_ISSUES_TOOL = {
    "type": "function",
    "name": "get_gin_open_issues_count",
    "description": "Get the current number of open issues for the Gin framework repository on GitHub. Use this only when the user asks how many open issues Gin has.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}


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


def answer_with_model_tool_choice(client: OpenAI, model: str, user_question: str) -> str | None:
    first_response = client.responses.create(
        model=model,
        input=user_question,
        tools=[GIN_RELEASE_TOOL, GIN_ISSUES_TOOL],
    )

    function_call = None
    for item in first_response.output:
        if item.type == "function_call" and item.name in {
            "get_gin_release_info",
            "get_gin_open_issues_count",
        }:
            function_call = item
            break

    if function_call is None:
        return None

    if function_call.name == "get_gin_release_info":
        tool_result = external_tool.call_release_tool()
    else:
        tool_result = external_tool.call_issues_tool()

    second_response = client.responses.create(
        model=model,
        previous_response_id=first_response.id,
        input=[
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": json.dumps(tool_result),
            }
        ],
    )

    return second_response.output_text


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
    grounded_rag_prompt = build_grounded_rag_prompt(USER_QUESTION, retrieved_context)

    load_dotenv()
    require_api_key()
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    client = OpenAI()

    tool_answer = answer_with_model_tool_choice(client, model, USER_QUESTION)

    grounded_answer = call_responses_api(client, model, grounded_rag_prompt)

    print("MODEL TOOL CHOICE RESULT")
    if tool_answer is None:
        print("No tool call. Falling back to grounded RAG result.")
        print(format_final_report(USER_QUESTION, retrieval_results, grounded_answer))
    else:
        print(tool_answer)
    print()



if __name__ == "__main__":
    main()
