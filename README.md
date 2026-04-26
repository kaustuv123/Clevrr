# Shopify Analyst

This repository implements a minimal, explainable Shopify analytics assistant with:
- **Backend:** FastAPI + LangGraph ReAct + LangChain tools
- **Frontend:** React + Vite + TypeScript
- **Data source:** Shopify Admin REST API (GET-only)
- **LLM:** Gemini (`GEMINI_API_KEY` + `GEMINI_MODEL` from env)

## What it supports now
The app is built around read-only Shopify analytics questions, including:
- Orders placed in the last 7 days
- Top-selling products last month / this month
- Revenue grouped by city
- Repeat customers
- Average order value trends
- Sales-based product promotion recommendations

The runtime path uses live Shopify data only. There is no fixture fallback in normal app usage.

## Architecture
- `POST /api/chat` handles one chat turn.
- `session_id` maps to LangGraph thread memory (per-session context).
- The configured Shopify store is the default source of truth.
- `store_url` is optional in the API request. If provided, it must match the configured store.
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
- Frontend renders typed `blocks[]` (`text`, `table`), compact sample-question tiles, loading stages, response metadata, and a sanitized debug panel.

## Agent prompt strategy
System instructions enforce:
1. read-only operations only
2. exact unsafe-operation refusal: `"This operation is not permitted."`
3. no raw code in user-facing output
4. tool-based analysis and grounded metrics
5. concise business-style responses in a strict JSON shape

## Frontend behavior
- Header shows only the app name: `Shopify Analyst`.
- The user does not need to enter a store URL.
- Sample questions appear as small clickable tiles in a manually scrollable picker.
- Clicking a sample fills the textarea.
- Loading uses rotating client-side stages:
  - Reading Shopify context
  - Fetching store data
  - Running analysis
  - Preparing the answer
- Assistant responses render as clean panels; tables use sticky headers, zebra rows, and horizontal overflow protection.

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

Optional store override, only accepted when it matches the configured store:
```json
{
  "message": "How many orders did we get in the last 7 days?",
  "session_id": "session-123",
  "store_url": "your-store.myshopify.com"
}
```

If `store_url` is omitted, the backend uses `SHOP_NAME` from the environment. `SHOPIFY_SHOP_NAME` remains supported for compatibility.

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
- No token streaming in this version; chat uses normal request/response calls.
- Chart rendering is deferred. The response contract is ready for typed UI blocks, but the frontend currently renders text and tables.
- LangSmith tracing is not wired. The app instead returns a sanitized local debug trace.
- Query quality depends on Shopify API availability and the configured Gemini model's tool-calling stability.
- Pagination is intentionally capped to keep calls bounded; responses mark `partial_data` when capped data may affect the answer.
- Runtime uses live Shopify data only; this is intentional so the assistant stays grounded in the connected store.

## Sample questions
1. How many orders were placed in the last 7 days?
2. Which products sold the most last month?
3. Show a table of revenue by city.
4. Who are my repeat customers?
5. What is the AOV trend this month?
6. Can you recommend what product to promote based on sales?
