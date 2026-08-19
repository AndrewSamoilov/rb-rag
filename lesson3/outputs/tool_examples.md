# External Tools for Gin Chatbot

## Tool overview

У цьому завданні до RAG chatbot-а додано два зовнішні read-only tools, які отримують актуальні дані з GitHub API.

Загальний pipeline:

```text
user question -> OpenAI tool choice -> Python tool call -> GitHub API -> normalized result -> final answer
```

Якщо модель не викликає tool, система повертається до звичайного grounded RAG pipeline.

## Tool 1: get_gin_release_info

Type: read API tool

Purpose: отримати останній реліз Gin framework з GitHub Releases API.

Source:

```text
https://api.github.com/repos/gin-gonic/gin/releases
```

When to use:

- коли користувач питає про latest/current/newest Gin version;
- коли користувач питає про останній release;
- коли користувач питає про changelog останнього релізу.

When not to use:

- для звичайних питань по документації Gin;
- для питань типу middleware, routing, graceful shutdown, binding JSON.

Input contract:

```json
{}
```

Output contract:

```json
{
  "tag_name": "v1.12.0",
  "published_at": "2026-02-28T...",
  "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0",
  "body": "release notes"
}
```

Validation:

- перевіряємо, що GitHub повернув не порожній список релізів;
- перевіряємо, що останній реліз має поля `tag_name`, `published_at`, `html_url`, `body`;
- якщо щось не так, wrapper повертає `{"error": "..."}`.

## Tool 2: get_gin_open_issues_count

Type: read API tool

Purpose: отримати актуальну кількість відкритих issues у репозиторії Gin.

Source:

```text
https://api.github.com/search/issues?q=repo:gin-gonic/gin is:issue is:open
```

Important note: використовується GitHub Search API з `is:issue is:open`, щоб рахувати саме issues без pull requests.

When to use:

- коли користувач питає, скільки open issues є у Gin на GitHub;
- коли потрібна актуальна кількість issues.

When not to use:

- для питань по документації;
- для питань про релізи;
- для питань не про GitHub issues Gin.

Input contract:

```json
{}
```

Output contract:

```json
{
  "repository": "gin-gonic/gin",
  "open_issues_count": 604,
  "html_url": "https://github.com/gin-gonic/gin/issues"
}
```

Validation:

- перевіряємо, що GitHub Search API повернув поле `total_count`;
- якщо поле відсутнє або API падає, wrapper повертає `{"error": "..."}`.

## Example 1

User question: Gin last version

Tool called: `get_gin_release_info`

Input:

```json
{}
```

Result:

```json
{
  "tag_name": "v1.12.0",
  "published_at": "2026-02-28T...",
  "html_url": "https://github.com/gin-gonic/gin/releases/tag/v1.12.0",
  "body": "..."
}
```

Final answer:

```text
The latest version of Gin is v1.12.0, published on February 28, 2026.
Release page: https://github.com/gin-gonic/gin/releases/tag/v1.12.0
```

Why tool is better than retrieval:

Версії постійно змінюються. Локальний retrieval працює по документації, яка була завантажена раніше, тому він не може надійно знати останню версію. У цьому прикладі RAG відповів, що не має достатньо інформації, а tool дав актуальні дані з GitHub.

## Example 2

User question: how to implement graceful shutdown

Tool called: none

Input:

```json
{}
```

Result:

```text
No tool call. Falling back to grounded RAG result.
```

Final answer:

```text
To implement a graceful shutdown in Gin, use Go's http.Server Shutdown method or supported third-party packages. The answer is based on retrieved Gin documentation chunks.
```

Why tool is better than retrieval:

У цьому випадку tool не кращий. Graceful shutdown - це документаційне питання, а не актуальні live-дані. Тому модель не викликала GitHub tool, і система правильно повернулася до grounded RAG.

## Example 3

User question: how many issues are open on github?

Tool called: `get_gin_open_issues_count`

Input:

```json
{}
```

Result:

```json
{
  "repository": "gin-gonic/gin",
  "open_issues_count": 604,
  "html_url": "https://github.com/gin-gonic/gin/issues"
}
```

Final answer:

```text
There are currently 604 open issues on the Gin GitHub repository.
You can check them here: https://github.com/gin-gonic/gin/issues
```

Why tool is better than retrieval:

Кількість open issues постійно змінюється. Retrieval по локальній документації не може знати актуальний стан GitHub repository. Tool напряму звертається до GitHub Search API і повертає live count.

## Summary

Tools корисні, коли chatbot-у потрібні актуальні або структуровані дані, яких немає в локальному індексі. У цьому прикладі RAG добре працює для документації Gin, а tools краще підходять для live-даних: останньої версії та кількості відкритих issues.

Мінус підходу: для великої RAG-системи може знадобитися багато різних tools під різні типи live-запитів. Тому важливо робити tools вузькими, зрозумілими і з чітким описом, коли їх треба викликати.
