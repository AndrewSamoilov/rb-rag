from __future__ import annotations
import json
from pathlib import Path
from typing import Any


RAW_DIR = Path("/Users/andrew/rag/lesson3/data/raw")
PROCESSED_DIR = Path("/Users/andrew/rag/lesson3/data/processed")
OUTPUT_PATH = PROCESSED_DIR / "normalized_documents.jsonl"



def extract_markdown_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            return stripped_line.replace("# ", "", 1).strip()
    return None


def read_markdown_file(file_path: Path) -> dict[str, Any]:
    text = file_path.read_text(encoding="utf-8")

    normalized = normalize_text(text)
    title = extract_markdown_title(text) or file_path.stem.replace("_", " ").title()
    return {
        "document_id": file_path.stem,
        "source_file": str(file_path),
        "source_type": "markdown",
        "title": title,
        "text": normalized,
        "metadata": {
            "language": "en",
            "domain": "doc",
            "document_type": "documentation",
        },
    }


def load_raw_sources(raw_dir: Path) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for file_path in sorted(raw_dir.iterdir()):
        if file_path.suffix.lower() == ".md":
            documents.append(read_markdown_file(file_path))
        else:
            print(f"Warning: unsupported file type skipped: {file_path}")
    return documents


def save_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

def normalize_text(text: str) -> str:
    emojis = ["📰", "📖", "🔌"]
    clean_lines = []
    blank_streak = 0
    for line in text.splitlines():
        line = line.rstrip()

        if "[![" in line:
            continue

        for emoji in emojis:
            line = line.replace(emoji, "")

        if line == "":
            blank_streak += 1
            # Collapse repeated blank lines but keep single blank lines,
            # since chunk.py relies on them to detect paragraph/list boundaries.
            if blank_streak > 1:
                continue
        else:
            blank_streak = 0

        clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {RAW_DIR}. "
            "Please run this script from the project root."
        )

    documents = load_raw_sources(RAW_DIR)


    
    save_jsonl(documents, OUTPUT_PATH)

    print("=" * 80)
    print("LESSON 3 DEMO 1: NORMALIZE SOURCES")
    print("=" * 80)
    print(f"Raw directory: {RAW_DIR}")
    print(f"Normalized documents: {len(documents)}")
    print(f"Output file: {OUTPUT_PATH}")
    print()

    for doc in documents:
        print("-" * 80)
        print(f"Document ID: {doc['document_id']}")
        print(f"Source type: {doc['source_type']}")
        print(f"Title: {doc['title']}")
        preview = doc["text"][:180].replace("\n", " ")
        print(f"Text preview: {preview}...")


if __name__ == "__main__":
    main()