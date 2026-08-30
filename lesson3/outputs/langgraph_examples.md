# Приклади LangGraph Workflow

## Обраний framework

Framework: `LangGraph`

Причина вибору: він напряму відповідає структурі workflow з HW6, тому що в рішенні вже є явний state, класифікація route, tool nodes і conditional branching.

## Визначення State

```python
class AgentState(TypedDict):
    user_question: str
    selected_route: RouteName
    steps: list[str]
    tool_calls: list[str]
    observations: list[dict]
    final_answer: str
```

## Структура графа

```text
START
-> classify_request
-> documentation_workflow -> run_documentation_lookup -> build_answer -> END
-> github_release_workflow -> run_release_lookup -> build_answer -> END
-> github_issues_workflow -> run_github_issues_lookup -> build_answer -> END
-> clarification -> ask_clarification -> build_answer -> END
```

## Приклад 1

Вхідне питання: `What is the latest Gin version?`

Обраний route: `github_release_workflow`

Виконані nodes: `classify_request -> run_release_lookup -> build_answer`

Фінальний state:

```json
{
  "user_question": "What is the latest Gin version?",
  "selected_route": "github_release_workflow",
  "steps": [
    "classify_request",
    "run_release_lookup",
    "build_answer"
  ],
  "tool_calls": [
    "mock_get_latest_gin_release"
  ],
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

Фінальна відповідь: The latest Gin release is v1.12.0, published on 2026-02-28. Release page: https://github.com/gin-gonic/gin/releases/tag/v1.12.0

## Приклад 2

Вхідне питання: `How do I implement graceful shutdown in Gin?`

Обраний route: `documentation_workflow`

Виконані nodes: `classify_request -> run_documentation_lookup -> build_answer`

Фінальний state:

```json
{
  "user_question": "How do I implement graceful shutdown in Gin?",
  "selected_route": "documentation_workflow",
  "steps": [
    "classify_request",
    "run_documentation_lookup",
    "build_answer"
  ],
  "tool_calls": [
    "mock_search_gin_docs"
  ],
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

Фінальна відповідь: According to Gin documentation: Use Go's http.Server Shutdown method with a context timeout to implement graceful shutdown in Gin. Source: doc_chunk_118.

## Приклад 3

Вхідне питання: `How many open issues does Gin have on GitHub?`

Обраний route: `github_issues_workflow`

Виконані nodes: `classify_request -> run_github_issues_lookup -> build_answer`

Фінальний state:

```json
{
  "user_question": "How many open issues does Gin have on GitHub?",
  "selected_route": "github_issues_workflow",
  "steps": [
    "classify_request",
    "run_github_issues_lookup",
    "build_answer"
  ],
  "tool_calls": [
    "mock_get_open_issues_count"
  ],
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

Фінальна відповідь: The gin-gonic/gin repository currently has 604 open issues. Issues page: https://github.com/gin-gonic/gin/issues

## Приклад 4

Вхідне питання: `I want to vacation?`

Обраний route: `clarification`

Виконані nodes: `classify_request -> ask_clarification -> build_answer`

Фінальний state:

```json
{
  "user_question": "I want to vacation?",
  "selected_route": "clarification",
  "steps": [
    "classify_request",
    "ask_clarification",
    "build_answer"
  ],
  "tool_calls": [],
  "observations": [],
  "final_answer": "Could you clarify your question? I can help with Gin documentation, the latest Gin release, or the current number of open GitHub issues."
}
```

Фінальна відповідь: Could you clarify your question? I can help with Gin documentation, the latest Gin release, or the current number of open GitHub issues.

## Порівняння custom flow vs framework

### Що стало краще

З `LangGraph` структура workflow стала більш явною. Тепер окремо видно state, nodes і переходи між ними, а не всю логіку в одному `if/elif` блоці. Це зручніше читати, пояснювати і розширювати, якщо з'являться нові route або додаткові кроки між ними.

### Що стало складніше

Для такого невеликого бота framework додає більше коду і трохи більше boilerplate. У custom flow усе можна було досить просто написати вручну в одній функції, і для 3-4 сценаріїв цього цілком вистачає. З framework треба окремо описувати graph, nodes, edges і слідкувати, щоб назви route та node всюди збігалися.

### Чи допоміг framework

Для цього розміру задачі можна було спокійно залишитись на custom implementation, бо бот маленький і логіка в ньому проста. Але framework корисний тим, що дає кращу основу для масштабування: якщо потім додати більше route, окремі tool chains, retries, memory або складнішу branching logic, така структура буде підтримуватись значно легше, ніж велика ручна функція з багатьма умовами.
