# Agentic Workflow for Gin Chatbot

## Domain and use case

Domain area: Gin framework assistant for developers.

Use case: користувач ставить питання про Gin. Agent повинен вирішити, чи це питання по документації, по актуальному релізу, по GitHub issues, або питання неясне і треба попросити уточнення.

## Workflow schema

```text
User question
-> Router
-> documentation_workflow -> mock_search_gin_docs -> Observation -> Final answer
-> github_release_workflow -> mock_get_latest_gin_release -> Observation -> Final answer
-> github_issues_workflow -> mock_get_open_issues_count -> Observation -> Final answer
-> clarification -> Ask user to clarify
```


## State

The workflow keeps this state during one run:

```json
{
  "user_goal": "original user question",
  "selected_route": "selected workflow route",
  "steps": ["route_question", "call_tool", "write_final_answer"],
  "tool_calls": ["tool function name"],
  "observations": [{"tool": "result"}],
  "final_answer": "answer shown to the user"
}
```

## Example 1

Question: What is the latest Gin version?

Route: `github_release_workflow`

Tool called: `mock_get_latest_gin_release`

Observation:

```json
{
  "tag_name": "v1.12.0",
  "published_at": "2026-02-28",
  "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0"
}
```

State after step:

```json
{
  "user_goal": "What is the latest Gin version?",
  "selected_route": "github_release_workflow",
  "steps": ["route_question", "call_release_tool", "write_final_answer"],
  "tool_calls": ["mock_get_latest_gin_release"],
  "observations": [
    {
      "tag_name": "v1.12.0",
      "published_at": "2026-02-28",
      "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0"
    }
  ],
  "final_answer": "The latest Gin release is v1.12.0, published on 2026-02-28. Release page: https://github.com/gin-gonic/gin/releases/tag/v1.12.0"
}
```

Final answer: The latest Gin release is v1.12.0, published on 2026-02-28. Release page: https://github.com/gin-gonic/gin/releases/tag/v1.12.0

## Example 2

Question: How do I implement graceful shutdown in Gin?

Route: `documentation_workflow`

Tool called: `mock_search_gin_docs`

Observation:

```json
{
  "source": "Gin documentation",
  "content": "Use Go's http.Server Shutdown method with a context timeout to implement graceful shutdown in Gin.",
  "chunk_id": "doc_chunk_118"
}
```

State after step:

```json
{
  "user_goal": "How do I implement graceful shutdown in Gin?",
  "selected_route": "documentation_workflow",
  "steps": ["route_question", "call_documentation_tool", "write_final_answer"],
  "tool_calls": ["mock_search_gin_docs"],
  "observations": [
    {
      "source": "Gin documentation",
      "content": "Use Go's http.Server Shutdown method with a context timeout to implement graceful shutdown in Gin.",
      "chunk_id": "doc_chunk_118"
    }
  ],
  "final_answer": "According to Gin documentation: Use Go's http.Server Shutdown method with a context timeout to implement graceful shutdown in Gin. Source: doc_chunk_118."
}
```

Final answer: According to Gin documentation: use Go's `http.Server` `Shutdown` method with a context timeout to implement graceful shutdown in Gin. Source: `doc_chunk_118`.

## Example 3

Question: How many open issues does Gin have on GitHub?

Route: `github_issues_workflow`

Tool called: `mock_get_open_issues_count`

Observation:

```json
{
  "repository": "gin-gonic/gin",
  "open_issues_count": 604,
  "html_url": "https://github.com/gin-gonic/gin/issues"
}
```

State after step:

```json
{
  "user_goal": "How many open issues does Gin have on GitHub?",
  "selected_route": "github_issues_workflow",
  "steps": ["route_question", "call_issues_tool", "write_final_answer"],
  "tool_calls": ["mock_get_open_issues_count"],
  "observations": [
    {
      "repository": "gin-gonic/gin",
      "open_issues_count": 604,
      "html_url": "https://github.com/gin-gonic/gin/issues"
    }
  ],
  "final_answer": "The gin-gonic/gin repository currently has 604 open issues. Issues page: https://github.com/gin-gonic/gin/issues"
}
```

Final answer: The `gin-gonic/gin` repository currently has 604 open issues. Issues page: https://github.com/gin-gonic/gin/issues

## Example 4

Question: Tell me something interesting.

Route: `clarification`

Tool called: none

Observation:

```json
null
```

State after step:

```json
{
  "user_goal": "Tell me something interesting.",
  "selected_route": "clarification",
  "steps": ["route_question", "ask_clarification"],
  "tool_calls": [],
  "observations": [],
  "final_answer": "Could you clarify your question? I can help with Gin documentation, the latest Gin release, or the current number of open GitHub issues."
}
```

Final answer: Could you clarify your question? I can help with Gin documentation, the latest Gin release, or the current number of open GitHub issues.
