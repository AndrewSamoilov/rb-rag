from __future__ import annotations

import argparse
import csv
import os
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import langgraph_flow


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
FIELD_NAMES = [
    "id",
    "question",
    "expected_behavior",
    "answer",
    "retrieved_chunks",
    "route_or_mode",
    "tools_used",
    "task_success",
    "groundedness",
    "answer_quality",
    "latency_ms",
    "errors",
    "notes",
    "trace_steps",
]


@dataclass(frozen=True)
class EvalCase:
    case_id: int
    question: str
    expected_behavior: str
    expected_route: str
    expected_terms: tuple[str, ...] = ()


EVAL_CASES = [
    EvalCase(
        1,
        "How do I define a GET route in Gin?",
        "Відповісти за документацією Gin про маршрутизацію і навести retrieved chunks.",
        "RAG",
        ("GET",),
    ),
    EvalCase(
        2,
        "How do I configure middleware and recovery in Gin?",
        "Знайти інструкції щодо middleware, пояснити налаштування й навести джерела.",
        "RAG",
        ("middleware", "recovery"),
    ),
    EvalCase(
        3,
        "How do I bind a JSON request body in Gin?",
        "Знайти документацію щодо request binding і відповісти з посиланнями на chunks.",
        "RAG",
        ("JSON",),
    ),
    EvalCase(
        4,
        "How do I skip logging for selected Gin paths?",
        "Використати retrieval документації; кейс перевіряє розпізнавання питання про logging.",
        "RAG",
        ("log",),
    ),
    EvalCase(
        5,
        "How should Gin support quantum teleportation middleware?",
        "Використати RAG і сказати, що retrieved context не містить цієї інформації.",
        "RAG",
        ("I do not have enough information",),
    ),
    EvalCase(
        6,
        "What is the latest Gin version?",
        "Викликати GitHub release tool і повернути його актуальний результат.",
        "tool:release",
    ),
    EvalCase(
        7,
        "How many open issues does Gin have on GitHub?",
        "Викликати GitHub issues tool і повернути його актуальний результат.",
        "tool:issues",
    ),
    EvalCase(
        8,
        "Tell me something interesting.",
        "Попросити користувача уточнити запит, а не вигадувати відповідь.",
        "clarification",
        ("clarify",),
    ),
    EvalCase(
        9,
        "Where should I ask a Gin deployment question?",
        "Знайти contributing guide і порадити Discussions Forum.",
        "RAG",
        ("discussion",),
    ),
    EvalCase(
        10,
        "What version and middleware changes should I adopt?",
        "Попросити уточнення, бо запит поєднує актуальний реліз і питання з документації.",
        "clarification",
        ("clarify",),
    ),
]


OFFLINE_RETRIEVED_CHUNKS = [
    {
        "chunk_id": "doc_chunk_routing",
        "text": "Gin supports routes such as GET and POST.",
        "metadata": {"title": "Routing", "source_file": "data/raw/doc.md"},
        "score": 0.03,
    },
    {
        "chunk_id": "doc_chunk_middleware",
        "text": "Gin middleware can provide logging and recovery.",
        "metadata": {"title": "Middleware", "source_file": "data/raw/doc.md"},
        "score": 0.03,
    },
    {
        "chunk_id": "doc_chunk_binding",
        "text": "Gin supports JSON request binding and validation.",
        "metadata": {"title": "Request Binding", "source_file": "data/raw/doc.md"},
        "score": 0.03,
    },
]


def configure_offline_fixtures() -> None:
    class OfflineResponse:
        def __init__(self, output_text: str) -> None:
            self.output_text = output_text

    class OfflineResponses:
        def create(self, *, input: str, **_: object) -> OfflineResponse:
            question = input.rsplit("User question:\n", maxsplit=1)[-1].split("\nAnswer:", maxsplit=1)[0].lower()
            if "quantum" in question:
                return OfflineResponse("I do not have enough information in the provided context.")
            if "middleware" in question:
                return OfflineResponse(
                    "Configure middleware and recovery with Gin middleware. "
                    "(doc_chunk_middleware)"
                )
            if "json" in question or "bind" in question:
                return OfflineResponse(
                    "Use Gin JSON request binding and validation. (doc_chunk_binding)"
                )
            return OfflineResponse("Use Gin GET routes. (doc_chunk_routing)")

    class OfflineClient:
        responses = OfflineResponses()

    os.environ.setdefault("OPENAI_API_KEY", "offline-evaluation-key")
    langgraph_flow.hybrid_search_retrieval.retrieval = lambda _question: OFFLINE_RETRIEVED_CHUNKS
    langgraph_flow.OpenAI = OfflineClient
    langgraph_flow.external_tool.call_release_tool = lambda: {
        "tag_name": "v1.12.0",
        "published_at": "2026-02-28",
        "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0",
    }
    langgraph_flow.external_tool.call_issues_tool = lambda: {
        "repository": "gin-gonic/gin",
        "open_issues_count": 604,
        "html_url": "https://github.com/gin-gonic/gin/issues",
    }


def route_or_mode(state: dict) -> str:
    route = state["selected_route"]
    if route == "documentation_workflow":
        return "RAG"
    if route == "github_release_workflow":
        return "tool:release"
    if route == "github_issues_workflow":
        return "tool:issues"
    return "clarification"


def retrieved_chunk_ids(state: dict) -> str:
    return ", ".join(chunk.get("chunk_id", "unknown") for chunk in state["retrieved_chunks"]) or "none"


def detect_errors(state: dict, actual_mode: str, case: EvalCase) -> list[str]:
    errors = []
    answer = state["final_answer"].lower()

    if actual_mode != case.expected_route:
        errors.append("wrong_route")
    if any("error" in observation for observation in state["observations"]):
        errors.append("tool_or_retrieval_error")
    if "could not generate a grounded answer" in answer:
        errors.append("generation_error")
    if "openai_api_key is not set" in answer:
        errors.append("missing_api_key")
    if actual_mode == "RAG" and not state["retrieved_chunks"]:
        errors.append("missing_context")
    return errors


def evaluate_case(case: EvalCase) -> dict[str, str | int]:
    started_at = time.perf_counter()
    state = langgraph_flow.run_agent(case.question)
    latency_ms = round((time.perf_counter() - started_at) * 1000)
    actual_mode = route_or_mode(state)
    answer = state["final_answer"]
    answer_lower = answer.lower()
    errors = detect_errors(state, actual_mode, case)
    expected_terms_found = all(term.lower() in answer_lower for term in case.expected_terms)

    if actual_mode in {"tool:release", "tool:issues", "clarification"}:
        groundedness = "not_applicable"
    elif errors or not state["retrieved_chunks"]:
        groundedness = "bad"
    elif any(chunk_id in answer for chunk_id in retrieved_chunk_ids(state).split(", ")):
        groundedness = "good"
    else:
        groundedness = "partial"

    if errors or not expected_terms_found:
        answer_quality = "bad" if actual_mode != case.expected_route or errors else "partial"
    else:
        answer_quality = "good"

    if not errors and expected_terms_found:
        task_success = "yes"
    elif actual_mode == case.expected_route and answer:
        task_success = "partial"
    else:
        task_success = "no"

    notes = "Відповідає очікуваному маршруту та перевіркам відповіді."
    if errors:
        notes = "Автоматичні перевірки виявили: " + ", ".join(errors) + "."
    elif not expected_terms_found:
        notes = "У відповіді не знайдено очікуваних термінів."

    return {
        "id": case.case_id,
        "question": case.question,
        "expected_behavior": case.expected_behavior,
        "answer": answer,
        "retrieved_chunks": retrieved_chunk_ids(state),
        "route_or_mode": actual_mode,
        "tools_used": ", ".join(state["tool_calls"]) or "none",
        "task_success": task_success,
        "groundedness": groundedness,
        "answer_quality": answer_quality,
        "latency_ms": latency_ms,
        "errors": ", ".join(errors) or "none",
        "notes": notes,
        "trace_steps": " -> ".join(state["steps"]),
    }


def write_results(rows: list[dict[str, str | int]], output_dir: Path) -> Path:
    output_path = output_dir / "eval_results.csv"
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def summary_values(rows: list[dict[str, str | int]]) -> dict[str, object]:
    total_cases = len(rows)
    success_count = sum(row["task_success"] == "yes" for row in rows)
    partial_count = sum(row["task_success"] == "partial" for row in rows)
    grounded_good_count = sum(row["groundedness"] == "good" for row in rows)
    latency_values = [int(row["latency_ms"]) for row in rows]
    error_counts = Counter(
        error
        for row in rows
        for error in str(row["errors"]).split(", ")
        if error != "none"
    )
    return {
        "total_cases": total_cases,
        "success_count": success_count,
        "partial_count": partial_count,
        "grounded_good_count": grounded_good_count,
        "average_latency_ms": round(sum(latency_values) / total_cases) if total_cases else 0,
        "max_latency_ms": max(latency_values, default=0),
        "error_counts": error_counts,
    }


def write_summary(
    rows: list[dict[str, str | int]], output_dir: Path, execution_mode: str
) -> tuple[Path, dict[str, object]]:
    metrics = summary_values(rows)
    total_cases = int(metrics["total_cases"])
    success_count = int(metrics["success_count"])
    partial_count = int(metrics["partial_count"])
    grounded_good_count = int(metrics["grounded_good_count"])
    error_counts = metrics["error_counts"]
    error_lines = [f"- `{error}`: {count}" for error, count in error_counts.most_common()]
    if not error_lines:
        error_lines = ["- `none`: 0"]
    error_block = "\n".join(error_lines)

    content = f"""# Підсумок оцінювання — LangGraph Gin Assistant

## Метрики запуску

- Усього кейсів: {total_cases}
- Success rate: {success_count}/{total_cases} = {success_count / total_cases:.0%}
- Partial success rate: {partial_count}/{total_cases} = {partial_count / total_cases:.0%}
- Groundedness good: {grounded_good_count}/{total_cases} = {grounded_good_count / total_cases:.0%}
- Середня затримка: {metrics['average_latency_ms']:,} мс
- Максимальна затримка: {metrics['max_latency_ms']:,} мс

## Найпоширеніші типи помилок

{error_block}

## Методика

Режим виконання: `{execution_mode}`.

Evaluator вимірює end-to-end latency навколо `langgraph_flow.run_agent()`, фіксує trace state та tool calls, а також виконує детерміновані перевірки очікуваного маршруту, обов'язкових термінів у відповіді, цитування retrieved chunks і зафіксованих помилок. Значення `not_applicable` для groundedness використовується для tool і clarification маршрутів, оскільки вони не застосовують retrieval документації.
"""
    output_path = output_dir / "eval_summary.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path, metrics


def write_quality_report(
    rows: list[dict[str, str | int]],
    metrics: dict[str, object],
    output_dir: Path,
    execution_mode: str,
) -> Path:
    total_cases = int(metrics["total_cases"])
    success_count = int(metrics["success_count"])
    error_counts = metrics["error_counts"]
    route_failures = sum("wrong_route" in str(row["errors"]) for row in rows)
    generation_failures = sum("generation_error" in str(row["errors"]) for row in rows)
    missing_context = sum("missing_context" in str(row["errors"]) for row in rows)

    content = f"""# Звіт про якість — LangGraph Gin Assistant

## Що тестувалося

Оцінювання запускає {total_cases} питань через LangGraph workflow. Набір покриває прямі питання до документації Gin, request binding, запит про logging, який маршрутизація може не розпізнати, непідтримуваний запит із очікуваною відповіддю «недостатньо інформації», обидва GitHub tools, clarification-запит, питання за contributing guide і multi-intent питання. Цей артефакт згенеровано в режимі `{execution_mode}`.

## Результати

- Загальна успішність: {success_count}/{total_cases} ({success_count / total_cases:.0%})
- Середня end-to-end затримка: {metrics['average_latency_ms']:,} мс
- Найчастіші зафіксовані помилки: {", ".join(error_counts) if error_counts else "none"}

## Де система працює добре

Граф записує кожен вибраний маршрут, tool call, ID retrieved chunk, відповідь і latency у `eval_results.csv`. Окремі tool-гілки роблять операції з релізом і кількістю issues спостережуваними, а RAG-гілка зберігає retrieved chunks окремо від tool observations. Завдяки цьому можна простежити невдалий результат до routing, retrieval, generation або зовнішньої залежності.

## Де система має проблеми

Детерміновані перевірки виявили {route_failures} невідповідностей маршруту, {missing_context} RAG-кейсів без придатного context і {generation_failures} збоїв grounded generation. Ці значення згенеровано поточним запуском, а не оцінено вручну.

## 3 головні проблеми

1. **Keyword-only routing є крихким.** Класифікатор розпізнає лише невеликий фіксований словник, тому документаційні запити на кшталт logging або contributing можуть потрапити в clarification чи GitHub tool замість retrieval.
2. **Покриття retrieval обмежене.** Поточний hybrid retriever застосовує фіксований metadata filter `document_id == "doc"`; він може виключити релевантні chunks із README та contributing guide.
3. **RAG не має fallback-відповіді після збою generation.** Якщо OpenAI request завершується помилкою, граф повертає рядок з помилкою, хоча вже міг отримати релевантні chunks; потрібен extractive fallback із цитуванням.

## Наступні кроки

Замінити keyword routing на intent classifier або явний RAG default для Gin-питань, зробити metadata filter retriever-а налаштовуваним, додати мінімальний поріг релевантності перед generation і повертати extractive відповідь, коли модель або мережа недоступна. Після кожної зміни повторно запускати `python scripts/evaluate_langgraph.py`, щоб порівнювати CSV і метрики.
"""
    output_path = output_dir / "quality_report.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the LangGraph Gin assistant.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--offline-fixtures",
        action="store_true",
        help="Run the graph with deterministic local retrieval, model, and GitHub adapters.",
    )
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    execution_mode = "offline-fixtures" if arguments.offline_fixtures else "live-services"
    if arguments.offline_fixtures:
        configure_offline_fixtures()

    rows = [evaluate_case(case) for case in EVAL_CASES]
    results_path = write_results(rows, arguments.output_dir)
    summary_path, metrics = write_summary(rows, arguments.output_dir, execution_mode)
    report_path = write_quality_report(rows, metrics, arguments.output_dir, execution_mode)

    print(f"Wrote {results_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
