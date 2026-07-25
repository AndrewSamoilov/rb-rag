# Висновки

Репозиторій: https://github.com/AndrewSamoilov/rb-rag/tree/main/lesson3

## Що взяв за дані

Обрав як сирі дані документацію вебфреймворка на Go - **Gin**. MD-файли лежать у `data/raw/`.

## Приклади чанків

**Чанк з блоком коду:**

```json
{"chunk_id": "doc_chunk_019", "text": "```go\nfunc main() {\n  router := gin.Default()\n  // Set a lower memory limit for multipart forms (default is 32 MiB)\n  router.MaxMultipartMemory = 8 << 20  // 8 MiB\n  router.POST(\"/upload\", func(c *gin.Context) {\n    // Single file\n    file, _ := c.FormFile(\"file\")\n    log.Println(file.Filename)\n\n    // Upload the file to specific dst.\n    c.SaveUploadedFile(file, dst)\n\n    c.String(http.StatusOK, fmt.Sprintf(\"'%s' uploaded!\", file.Filename))\n  })\n  router.Run(\":8080\")\n}\n```\n\nHow to `curl`:\n\n```bash\ncurl -X POST http://localhost:8080/upload \\\n  -F \"file=@/Users/appleboy/test.zip\" \\\n  -H \"Content-Type: multipart/form-data\"\n```\n\n#### Multiple files", "metadata": {"document_id": "doc", "source_file": "/Users/andrew/rag/lesson3/data/raw/doc.md", "source_type": "markdown", "title": "Gin Quick Start", "chunk_index": 19, "language": "en", "domain": "doc", "document_type": "documentation"}}
```

**Короткий чанк без коду:**

```json
{"chunk_id": "doc_chunk_057", "text": "### Bind Query String or Post Data\n\nSee the [detail information](https://github.com/gin-gonic/gin/issues/742#issuecomment-264681292).", "metadata": {"document_id": "doc", "source_file": "/Users/andrew/rag/lesson3/data/raw/doc.md", "source_type": "markdown", "title": "Gin Quick Start", "chunk_index": 57, "language": "en", "domain": "doc", "document_type": "documentation"}}
```

## Висновки

**Плюси:**

- Головна ціль була - не рвати код. Якщо в тексті є блок коду, він завжди залишається цілим в одному чанку, навіть якщо через це чанк вийде більшим за заданий розмір (700 символів). Приклад - `doc_chunk_019`, де два блоки коду (`go` і `bash`) разом з поясненням між ними влізли в один чанк, і жоден з них не розірваний посередині.
- Метадата (`document_id`, `title`, `chunk_index`, `source_file`) зберігається в кожному чанку, тож завжди видно, звідки взятий текст.

**Мінуси:**

- Чанки вийшли нерівномірні за розміром. Через те що код і абзаци не ріжуться навпіл, один чанк може бути 130 символів (`doc_chunk_057`), а інший - понад 700 (`doc_chunk_019`). Тобто пожертвував рівномірністю розміру заради цілісності коду.
- Дуже маленькі чанки (типу `doc_chunk_057` - просто заголовок і одне речення) не дуже інформативні самі по собі й можуть погано відпрацювати в пошуку.
