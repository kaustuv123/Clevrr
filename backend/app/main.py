from __future__ import annotations

import logging
from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
except Exception:  # noqa: BLE001
    ChatGoogleGenerativeAIError = Exception

from .agent import AgentService
from .config import get_settings
from .debug import RequestDebugState, reset_debug_state, set_debug_state
from .response_formatter import format_agent_output
from .schemas import ChatRequest, ChatResponse, ResponseMeta, TextBlock
from .security import is_unsafe_operation, unsafe_operation_message
from .shopify_client import ShopifyClientError, ShopifyValidationError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    agent_service = AgentService(settings=settings)

    app = FastAPI(title="Shopify Agent Backend", version="0.1.0")
    app.state.settings = settings
    app.state.agent_service = agent_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        service: AgentService = app.state.agent_service
        started_at = perf_counter()
        debug_state = RequestDebugState()
        debug_token = set_debug_state(debug_state)

        try:
            if request.store_url:
                service.shopify_client.validate_store_url(request.store_url)
            timezone_name = await service.get_timezone()

            if is_unsafe_operation(request.message):
                answer = unsafe_operation_message()
                blocks = [TextBlock(text=answer)]
                return ChatResponse(
                    answer=answer,
                    blocks=blocks,
                    meta=ResponseMeta(
                        timezone=timezone_name,
                        partial_data=False,
                        duration_ms=int((perf_counter() - started_at) * 1000),
                        session_id=request.session_id,
                    ),
                    debug=debug_state.to_payload(),
                )

            raw_content = await service.run(
                question=request.message,
                session_id=request.session_id,
            )
            answer, blocks, notes = format_agent_output(raw_content)
            for note in notes:
                debug_state.add_note(note)

            return ChatResponse(
                answer=answer,
                blocks=blocks,
                meta=ResponseMeta(
                    timezone=timezone_name,
                    partial_data=debug_state.partial_data,
                    duration_ms=int((perf_counter() - started_at) * 1000),
                    session_id=request.session_id,
                ),
                debug=debug_state.to_payload(),
            )
        except ShopifyValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ShopifyClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ChatGoogleGenerativeAIError as exc:
            logger.exception("Gemini API error in /api/chat")
            raise HTTPException(status_code=502, detail=f"Gemini API error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled error in /api/chat")
            detail = (
                f"{exc.__class__.__name__}: {exc}"
                if settings.debug_error_details
                else "Internal server error."
            )
            raise HTTPException(status_code=500, detail=detail) from exc
        finally:
            reset_debug_state(debug_token)

    return app


app = create_app()
