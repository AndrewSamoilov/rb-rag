from __future__ import annotations

import json
import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from openai import OpenAI

import external_tool
import hybrid_search_retrieval
from rag_answer import build_grounded_rag_prompt, format_retrieved_context

try:
    from langgraph.graph import END, START, StateGraph
except ImportError as exc:
    raise SystemExit(
        "LangGraph is not installed. Install it with `pip install langgraph` in your virtual environment."
    ) from exc


DEFAULT_MODEL = "gpt-4.1-mini"

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
    retrieved_chunks: list[dict]
    final_answer: str


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
    try:
        state["retrieved_chunks"] = hybrid_search_retrieval.retrieval(state["user_question"])
        state["tool_calls"].append("hybrid_search_retrieval.retrieval")
    except Exception as error:
        state["retrieved_chunks"] = []
        state["observations"].append({"error": str(error)})
    return state


def run_release_lookup(state: AgentState) -> AgentState:
    state["steps"].append("run_release_lookup")
    observation = external_tool.call_release_tool()
    state["tool_calls"].append("external_tool.call_release_tool")
    state["observations"].append(observation)
    return state


def run_github_issues_lookup(state: AgentState) -> AgentState:
    state["steps"].append("run_github_issues_lookup")
    observation = external_tool.call_issues_tool()
    state["tool_calls"].append("external_tool.call_issues_tool")
    state["observations"].append(observation)
    return state


def ask_clarification(state: AgentState) -> AgentState:
    state["steps"].append("ask_clarification")
    return state


def generate_grounded_answer(state: AgentState) -> AgentState:
    state["steps"].append("generate_grounded_answer")

    if not state["retrieved_chunks"]:
        state["final_answer"] = "I do not have enough information in the provided context."
        return state

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        state["final_answer"] = (
            "Retrieved documentation is available, but OPENAI_API_KEY is not set, "
            "so I cannot generate a grounded answer."
        )
        return state

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    prompt = build_grounded_rag_prompt(
        state["user_question"],
        format_retrieved_context(state["retrieved_chunks"]),
    )

    try:
        response = OpenAI().responses.create(model=model, input=prompt)
        state["final_answer"] = response.output_text
    except Exception as error:
        state["final_answer"] = f"Could not generate a grounded answer: {error}"

    return state


def build_tool_answer(state: AgentState) -> AgentState:
    state["steps"].append("build_tool_answer")
    observation = state["observations"][-1]

    if "error" in observation:
        state["final_answer"] = f"The tool request failed: {observation['error']}"
    elif state["selected_route"] == "github_release_workflow":
        state["final_answer"] = (
            f"The latest Gin release is {observation['tag_name']}, published on "
            f"{observation['published_at']}. Release page: {observation['html_url']}"
        )
    else:
        state["final_answer"] = (
            f"The {observation['repository']} repository currently has "
            f"{observation['open_issues_count']} open issues. "
            f"Issues page: {observation['html_url']}"
        )

    return state


def build_clarification_answer(state: AgentState) -> AgentState:
    state["steps"].append("build_clarification_answer")
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
    workflow.add_node("generate_grounded_answer", generate_grounded_answer)
    workflow.add_node("run_release_lookup", run_release_lookup)
    workflow.add_node("run_github_issues_lookup", run_github_issues_lookup)
    workflow.add_node("ask_clarification", ask_clarification)
    workflow.add_node("build_tool_answer", build_tool_answer)
    workflow.add_node("build_clarification_answer", build_clarification_answer)

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
    workflow.add_edge("run_documentation_lookup", "generate_grounded_answer")
    workflow.add_edge("generate_grounded_answer", END)
    workflow.add_edge("run_release_lookup", "build_tool_answer")
    workflow.add_edge("run_github_issues_lookup", "build_tool_answer")
    workflow.add_edge("build_tool_answer", END)
    workflow.add_edge("ask_clarification", "build_clarification_answer")
    workflow.add_edge("build_clarification_answer", END)

    return workflow.compile()


def initial_state(user_question: str) -> AgentState:
    return {
        "user_question": user_question,
        "selected_route": "clarification",
        "steps": [],
        "tool_calls": [],
        "observations": [],
        "retrieved_chunks": [],
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
