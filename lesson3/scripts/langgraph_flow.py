from __future__ import annotations

import json
from typing import Literal, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError as exc:
    raise SystemExit(
        "LangGraph is not installed. Install it with `pip install langgraph` in your virtual environment."
    ) from exc


RouteName = Literal[
    "documentation_workflow",
    "github_release_workflow",
    "github_issues_workflow",
    "clarification",
]


class AgentState(TypedDict):
    user_question: str
    selected_route: RouteName
    steps: list[str]
    tool_calls: list[str]
    observations: list[dict]
    final_answer: str


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


def classify_request(state: AgentState) -> AgentState:
    question_lower = state["user_question"].lower()
    state["steps"].append("classify_request")

    if any(word in question_lower for word in ["version", "release", "latest", "newest"]):
        state["selected_route"] = "github_release_workflow"
    elif "issue" in question_lower or "issues" in question_lower:
        state["selected_route"] = "github_issues_workflow"
    elif any(word in question_lower for word in ["shutdown", "middleware", "routing", "bind", "json"]):
        state["selected_route"] = "documentation_workflow"
    else:
        state["selected_route"] = "clarification"

    return state


def run_documentation_lookup(state: AgentState) -> AgentState:
    state["steps"].append("run_documentation_lookup")
    observation = mock_search_gin_docs(state["user_question"])
    state["tool_calls"].append("mock_search_gin_docs")
    state["observations"].append(observation)
    return state


def run_release_lookup(state: AgentState) -> AgentState:
    state["steps"].append("run_release_lookup")
    observation = mock_get_latest_gin_release()
    state["tool_calls"].append("mock_get_latest_gin_release")
    state["observations"].append(observation)
    return state


def run_github_issues_lookup(state: AgentState) -> AgentState:
    state["steps"].append("run_github_issues_lookup")
    observation = mock_get_open_issues_count()
    state["tool_calls"].append("mock_get_open_issues_count")
    state["observations"].append(observation)
    return state


def ask_clarification(state: AgentState) -> AgentState:
    state["steps"].append("ask_clarification")
    return state


def build_answer(state: AgentState) -> AgentState:
    state["steps"].append("build_answer")
    route = state["selected_route"]

    if route == "documentation_workflow":
        observation = state["observations"][-1]
        state["final_answer"] = (
            f"According to {observation['source']}: {observation['content']} "
            f"Source: {observation['chunk_id']}."
        )
    elif route == "github_release_workflow":
        observation = state["observations"][-1]
        state["final_answer"] = (
            f"The latest Gin release is {observation['tag_name']}, published on "
            f"{observation['published_at']}. Release page: {observation['html_url']}"
        )
    elif route == "github_issues_workflow":
        observation = state["observations"][-1]
        state["final_answer"] = (
            f"The {observation['repository']} repository currently has "
            f"{observation['open_issues_count']} open issues. "
            f"Issues page: {observation['html_url']}"
        )
    else:
        state["final_answer"] = (
            "Could you clarify your question? I can help with Gin documentation, "
            "the latest Gin release, or the current number of open GitHub issues."
        )

    return state


def route_after_classification(state: AgentState) -> RouteName:
    return state["selected_route"]


def build_app():
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_request", classify_request)
    workflow.add_node("run_documentation_lookup", run_documentation_lookup)
    workflow.add_node("run_release_lookup", run_release_lookup)
    workflow.add_node("run_github_issues_lookup", run_github_issues_lookup)
    workflow.add_node("ask_clarification", ask_clarification)
    workflow.add_node("build_answer", build_answer)

    workflow.add_edge(START, "classify_request")
    workflow.add_conditional_edges(
        "classify_request",
        route_after_classification,
        {
            "documentation_workflow": "run_documentation_lookup",
            "github_release_workflow": "run_release_lookup",
            "github_issues_workflow": "run_github_issues_lookup",
            "clarification": "ask_clarification",
        },
    )
    workflow.add_edge("run_documentation_lookup", "build_answer")
    workflow.add_edge("run_release_lookup", "build_answer")
    workflow.add_edge("run_github_issues_lookup", "build_answer")
    workflow.add_edge("ask_clarification", "build_answer")
    workflow.add_edge("build_answer", END)

    return workflow.compile()


def initial_state(user_question: str) -> AgentState:
    return {
        "user_question": user_question,
        "selected_route": "clarification",
        "steps": [],
        "tool_calls": [],
        "observations": [],
        "final_answer": "",
    }


def run_agent(question: str) -> AgentState:
    app = build_app()
    return app.invoke(initial_state(question))


def main() -> None:
    questions = [
        "What is the latest Gin version?",
        "How do I implement graceful shutdown in Gin?",
        "I want to vacation?",
    ]

    for question in questions:
        print(json.dumps(run_agent(question), indent=2))
        print()


if __name__ == "__main__":
    main()
