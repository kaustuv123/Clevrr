# Shopify Agent Assignment (Interview-First v1)

This repository implements a minimal, explainable Shopify analytics agent with:
- **Backend:** FastAPI + LangGraph ReAct + LangChain tools
- **Frontend:** React + Vite + TypeScript
- **Data source:** Shopify Admin REST API (GET-only)
- **LLM:** Gemini (`GEMINI_API_KEY` + `GEMINI_MODEL` from env)

## What this v1 supports
- Orders in last 7 days
- Top-selling products this month
- Repeat customers

## Architecture
- `POST /api/chat` handles one chat turn.
- `session_id` maps to LangGraph thread memory (per-session context).
- Tools:
  - `get_shopify_data` (canonical GET-only tool)
  - `get_orders_data`, `get_products_data`, `get_customers_data` (thin wrappers)
  - `get_time_windows` (shop-timezone based windows)
  - `python_repl_ast` (analysis helper)
- Shopify client includes:
  - GET-only enforcement
  - pagination with page cap + partial-data marker
  - 429 retry with backoff
  - malformed response handling
- Frontend renders typed `blocks[]` (`text`, `table`) and a sanitized debug panel.

## Agent prompt strategy
System instructions enforce:
1. read-only operations only
2. exact unsafe-operation refusal: `"This operation is not permitted."`
3. no raw code in user-facing output
4. tool-based analysis and grounded metrics
5. concise business-style responses in a strict JSON shape

## Setup (local)
1. Copy `.env.example` to `.env` and fill all values.
2. Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open `http://localhost:5173`.

## Setup (Docker Compose)
```bash
docker compose up --build
```
Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`

## API contract
`POST /api/chat`

Request:
```json
{
  "message": "How many orders did we get in the last 7 days?",
  "session_id": "session-123"
}
```

Store host is sourced from environment (`SHOP_NAME`; `SHOPIFY_SHOP_NAME` remains supported for compatibility).

Response:
```json
{
  "answer": "Business summary...",
  "blocks": [
    { "type": "text", "text": "..." },
    { "type": "table", "title": "Optional", "columns": ["..."], "rows": [["..."]] }
  ],
  "meta": {
    "timezone": "America/New_York",
    "partial_data": false,
    "duration_ms": 932,
    "session_id": "session-123"
  },
  "debug": {
    "tool_calls": [],
    "notes": []
  }
}
```

## Tests
- Backend:
  ```bash
  cd backend
  pytest -q
  ```
- Frontend:
  ```bash
  cd frontend
  npm test
  ```

## Known issues / limits
- V1 scope intentionally optimized for explainability over broad query coverage.
- LangSmith tracing is not wired in this version.
- Chart rendering is intentionally deferred.
- Live Shopify data only; no runtime fixture fallback.

## Sample questions
1. How many orders were placed in the last 7 days?
2. Which products sold the most last month?
3. Who are my repeat customers?

