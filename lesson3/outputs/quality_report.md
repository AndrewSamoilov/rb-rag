# Звіт про якість — LangGraph Gin Assistant

## Що тестувалося

Оцінювання запускає 10 питань через LangGraph workflow. Набір покриває прямі питання до документації Gin, request binding, запит про logging, який маршрутизація може не розпізнати, непідтримуваний запит із очікуваною відповіддю «недостатньо інформації», обидва GitHub tools, clarification-запит, питання за contributing guide і multi-intent питання. 

## Результати

- Загальна успішність: 6/10 (60%)
- Середня end-to-end затримка: 1,861 мс
- Найчастіші зафіксовані помилки: wrong_route

## Де система працює добре

Граф записує кожен вибраний маршрут, tool call, ID retrieved chunk, відповідь і latency у `eval_results.csv`. Окремі tool-гілки роблять операції з релізом і кількістю issues спостережуваними, а RAG-гілка зберігає retrieved chunks окремо від tool observations. Завдяки цьому можна простежити невдалий результат до routing, retrieval, generation або зовнішньої залежності.

## Де система має проблеми

Детерміновані перевірки виявили 4 невідповідностей маршруту, 0 RAG-кейсів без придатного context і 0 збоїв grounded generation. Ці значення згенеровано поточним запуском, а не оцінено вручну.

## 3 головні проблеми

1. **Keyword-only routing є крихким.** Класифікатор розпізнає лише невеликий фіксований словник, тому документаційні запити на кшталт logging або contributing можуть потрапити в clarification чи GitHub tool замість retrieval.
2. **Покриття retrieval обмежене.** Поточний hybrid retriever застосовує фіксований metadata filter `document_id == "doc"`; він може виключити релевантні chunks із README та contributing guide.
3. **RAG не має fallback-відповіді після збою generation.** Якщо OpenAI request завершується помилкою, граф повертає рядок з помилкою, хоча вже міг отримати релевантні chunks; потрібен extractive fallback із цитуванням.
