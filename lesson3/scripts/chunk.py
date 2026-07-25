
import json
import re
from pathlib import Path
from typing import Any

INPUT_PATH = Path("/Users/andrew/rag/lesson3/data/processed/normalized_documents.jsonl")
OUTPUT_PATH = Path("/Users/andrew/rag/lesson3/data/processed/chunks.jsonl")
CHUNK_SIZE = 700
CHUNK_OVERLAP = 150

FENCE_RE = re.compile(r"^(```|~~~)")


def load_jsonl(input_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as input_file:
        for line in input_file:
            stripped_line = line.strip()
            if stripped_line:
                records.append(json.loads(stripped_line))
    return records


def save_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")




def split_large_paragraph(paragraph: str, limit: int) -> list[str]:
    """Split an oversized prose paragraph on line boundaries, never mid-line."""
    lines = paragraph.splitlines()
    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        added_len = len(line) + (1 if current else 0)
        if current and current_len + added_len > limit:
            parts.append("\n".join(current))
            current = []
            current_len = 0
            added_len = len(line)
        current.append(line)
        current_len += added_len

    if current:
        parts.append("\n".join(current))

    return parts


def split_into_blocks(text: str, chunk_size: int) -> list[str]:
    """
    Split document text into atomic blocks: fenced code blocks (kept whole,
    since splitting them mid-fence produces invalid/truncated code) and
    prose paragraphs (split on blank lines, then on line boundaries if still
    oversized).
    """
    blocks: list[str] = []
    prose_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False

    def flush_prose() -> None:
        prose = "\n".join(prose_lines).strip()
        prose_lines.clear()
        if not prose:
            return
        for paragraph in re.split(r"\n\s*\n", prose):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(paragraph) > chunk_size:
                blocks.extend(split_large_paragraph(paragraph, chunk_size))
            else:
                blocks.append(paragraph)

    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            if in_code:
                code_lines.append(line)
                blocks.append("\n".join(code_lines))
                code_lines = []
                in_code = False
            else:
                flush_prose()
                in_code = True
                code_lines = [line]
        elif in_code:
            code_lines.append(line)
        else:
            prose_lines.append(line)

    if code_lines:
        # Unterminated fence: keep it whole rather than dropping content.
        blocks.append("\n".join(code_lines))
    flush_prose()

    return blocks


def pack_blocks(blocks: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Greedily pack atomic blocks into chunks, carrying trailing blocks as overlap."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def current_len_with(block: str) -> int:
        return current_len + (2 if current else 0) + len(block)

    index = 0
    while index < len(blocks):
        block = blocks[index]

        if current and current_len_with(block) > chunk_size:
            chunks.append("\n\n".join(current))

            carried: list[str] = []
            carried_len = 0
            for part in reversed(current):
                if carried_len + len(part) > overlap:
                    break
                carried.insert(0, part)
                carried_len += len(part)
            if len(carried) == len(current):
                # Nothing was dropped, so the next block still won't fit and we'd
                # loop forever re-emitting the same chunk. Drop the overlap here
                # to guarantee forward progress.
                carried = []
            current = carried
            current_len = sum(len(p) for p in current) + 2 * max(0, len(current) - 1)
            continue

        current.append(block)
        current_len = sum(len(p) for p in current) + 2 * max(0, len(current) - 1)
        index += 1

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def split_text_with_overlap(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into chunks, respecting markdown structure. Fenced code blocks
    are always kept whole; prose is packed by paragraph with a target overlap
    between consecutive chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    blocks = split_into_blocks(text, chunk_size)
    return pack_blocks(blocks, chunk_size, overlap)


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Create a stable, predictable chunk ID."""
    return f"{document_id}_chunk_{chunk_index:03d}"


def chunk_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Split one normalized document into metadata-rich chunks."""
    text_chunks = split_text_with_overlap(document["text"])
    chunks: list[dict[str, Any]] = []

    for index, chunk_text in enumerate(text_chunks, start=1):
        chunks.append(
            {
                "chunk_id": build_chunk_id(document["document_id"], index),
                "text": chunk_text,
                "metadata": {
                    "document_id": document["document_id"],
                    "source_file": document["source_file"],
                    "source_type": document["source_type"],
                    "title": document["title"],
                    "chunk_index": index,
                    "language": document["metadata"].get("language"),
                    "domain": document["metadata"].get("domain"),
                    "document_type": document["metadata"].get("document_type"),
                },
            }
        )

    return chunks


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Please run 01_normalize_sources.py first."
        )

    documents = load_jsonl(INPUT_PATH)
    all_chunks: list[dict[str, Any]] = []
    for document in documents:
        all_chunks.extend(chunk_document(document))

    save_jsonl(all_chunks, OUTPUT_PATH)

    print("=" * 80)
    print("=" * 80)
    print(f"Input documents: {len(documents)}")
    print(f"Output chunks: {len(all_chunks)}")
    print(f"Chunk size: {CHUNK_SIZE} characters")
    print(f"Chunk overlap: {CHUNK_OVERLAP} characters")
    print(f"Output file: {OUTPUT_PATH}")
    print()

    for chunk in all_chunks[:3]:
        print("-" * 80)
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['metadata']['source_file']}")
        print(f"Chunk index: {chunk['metadata']['chunk_index']}")
        preview = chunk["text"][:220].replace("\n", " ")
        print(f"Text preview: {preview}...")


if __name__ == "__main__":
    main()