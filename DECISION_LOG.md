# Decision Log (Interview Notes)

## 1) FastAPI over Flask/Django
- **Decision:** Use FastAPI async.
- **Why:** Typed request/response contracts and clean API boundaries make interview explanation easier.
- **Tradeoff:** Slightly more framework concepts than Flask.

## 2) LangGraph ReAct over classic AgentExecutor
- **Decision:** Use `create_react_agent` with `MemorySaver`.
- **Why:** Modern LangChain architecture with explicit thread memory (`session_id` -> `thread_id`).
- **Tradeoff:** Some API surface is newer and can evolve.

## 3) One canonical Shopify tool + endpoint wrappers
- **Decision:** Keep `get_shopify_data` plus `get_orders_data` / `get_products_data` / `get_customers_data`.
- **Why:** Meets assignment requirement while improving tool-selection reliability.
- **Tradeoff:** Slight duplication in wrapper arguments.

## 4) Capped pagination
- **Decision:** Stop after configured page cap and mark `partial_data`.
- **Why:** Prevents runaway latency/token costs in assignment environment.
- **Tradeoff:** Very broad queries may be partial; surfaced explicitly in metadata/debug notes.

## 5) Strict unsafe operation handling
- **Decision:** Exact sentence for write-intent requests.
- **Why:** Direct assignment compliance and deterministic behavior.
- **Tradeoff:** Less conversational nuance for unsafe requests.

## 6) Typed block response contract
- **Decision:** Backend returns `answer + blocks[] + meta + debug`.
- **Why:** Deterministic frontend rendering and interview-friendly interface contract.
- **Tradeoff:** Requires response formatting layer when model output is imperfect.

## 7) Non-streaming v1
- **Decision:** Request/response only.
- **Why:** Simpler state management and easier debugging for first pass.
- **Tradeoff:** No token-by-token UX.

