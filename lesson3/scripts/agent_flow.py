from __future__ import annotations

import json


def mock_search_gin_docs(question: str) -> dict:
    question_lower = question.lower()

    if "shutdown" in question_lower:
        return {
            "source": "Gin documentation",
            "content": "Use Go's http.Server Shutdown method with a context timeout to implement graceful shutdown in Gin.",
            "chunk_id": "doc_chunk_118",
        }

    if "middleware" in question_lower:
        return {
            "source": "Gin documentation",
            "content": "Gin middleware is a handler that can run before or after request handlers, for example for logging, authentication, or recovery.",
            "chunk_id": "doc_chunk_007",
        }

    return {
        "source": "Gin documentation",
        "content": "Use the Gin documentation to answer framework usage questions.",
        "chunk_id": "doc_chunk_unknown",
    }


def mock_get_latest_gin_release() -> dict:
    return {
        "tag_name": "v1.12.0",
        "published_at": "2026-02-28",
        "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0",
    }


def mock_get_open_issues_count() -> dict:
    return {
        "repository": "gin-gonic/gin",
        "open_issues_count": 604,
        "html_url": "https://github.com/gin-gonic/gin/issues",
    }


def route_question(question: str) -> str:
    question_lower = question.lower()

    if any(word in question_lower for word in ["version", "release", "latest", "newest"]):
        return "github_release_workflow"

    if "issue" in question_lower or "issues" in question_lower:
        return "github_issues_workflow"

    if any(word in question_lower for word in ["shutdown", "middleware", "routing", "bind", "json"]):
        return "documentation_workflow"

    return "clarification"


def run_agent(question: str) -> dict:
    state = {
        "user_goal": question,
        "selected_route": None,
        "steps": [],
        "tool_calls": [],
        "observations": [],
        "final_answer": None,
    }

    state["steps"].append("route_question")
    route = route_question(question)
    state["selected_route"] = route

    if route == "documentation_workflow":
        state["steps"].append("call_documentation_tool")
        observation = mock_search_gin_docs(question)
        state["tool_calls"].append("mock_search_gin_docs")
        state["observations"].append(observation)
        state["steps"].append("write_final_answer")
        state["final_answer"] = (
            f"According to {observation['source']}: {observation['content']} "
            f"Source: {observation['chunk_id']}."
        )

    elif route == "github_release_workflow":
        state["steps"].append("call_release_tool")
        observation = mock_get_latest_gin_release()
        state["tool_calls"].append("mock_get_latest_gin_release")
        state["observations"].append(observation)
        state["steps"].append("write_final_answer")
        state["final_answer"] = (
            f"The latest Gin release is {observation['tag_name']}, published on "
            f"{observation['published_at']}. Release page: {observation['html_url']}"
        )

    elif route == "github_issues_workflow":
        state["steps"].append("call_issues_tool")
        observation = mock_get_open_issues_count()
        state["tool_calls"].append("mock_get_open_issues_count")
        state["observations"].append(observation)
        state["steps"].append("write_final_answer")
        state["final_answer"] = (
            f"The {observation['repository']} repository currently has "
            f"{observation['open_issues_count']} open issues. "
            f"Issues page: {observation['html_url']}"
        )

    else:
        state["steps"].append("ask_clarification")
        state["final_answer"] = (
            "Could you clarify your question? I can help with Gin documentation, "
            "the latest Gin release, or the current number of open GitHub issues."
        )

    return state


def main() -> None:
    questions = [
        "What is the latest Gin version?",
        "How do I implement graceful shutdown in Gin?",
        "How many open issues does Gin have on GitHub?",
        "Tell me something interesting.",
    ]

    for question in questions:
        print(json.dumps(run_agent(question), indent=2))
        print()


if __name__ == "__main__":
    main()
