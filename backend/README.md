# Backend (FastAPI + LangGraph)

## Run locally
1. Create and activate a Python 3.12 virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure root `.env` has required keys:
   - `SHOP_NAME` (or legacy `SHOPIFY_SHOP_NAME`)
   - `SHOPIFY_API_VERSION`
   - `SHOPIFY_ACCESS_TOKEN`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`
4. Start API server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API contract
- `POST /api/chat`
   - request: `message`, `session_id`
  - response: `answer`, `blocks[]`, `meta`, `debug`

## Gemini model notes
- Tool-calling in this project is confirmed working with `gemini-2.5-pro`.
- Some preview models may fail in LangChain tool mode with thought-signature errors.
- If needed, enable detailed error payloads with `DEBUG_ERROR_DETAILS=true`.

## Tests
```bash
pytest -q
```
