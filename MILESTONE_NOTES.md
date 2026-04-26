# Milestone Notes

## Milestone 1: Backend skeleton
- Added FastAPI app and typed `/api/chat` contract.
- Added Shopify client with GET-only, pagination cap, 429 retry/backoff, malformed-response handling.
- Added store URL validation against configured store.

## Milestone 2: Agent + tools
- Wired LangGraph ReAct with Gemini model.
- Implemented canonical `get_shopify_data` and endpoint-specific wrappers.
- Added `PythonAstREPLTool` wrapper and timezone window helper tool.
- Added per-session memory using `session_id`.

## Milestone 3: Output shaping + safety
- Added strict unsafe-operation response behavior.
- Added response formatter for typed blocks.
- Added sanitized debug trace capture (tool calls, endpoint, retries, duration, notes).

## Milestone 4: Frontend
- Built React chat interface with store URL input, message history, loading/error handling.
- Implemented deterministic rendering for text/table blocks.
- Added debug panel for sanitized execution details.

## Milestone 5: Delivery
- Added backend and frontend Dockerfiles.
- Added root docker-compose setup.
- Added tests for backend core logic and frontend smoke rendering.
- Added README + decision log for interview preparation.

