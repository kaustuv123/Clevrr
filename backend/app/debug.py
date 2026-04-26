from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field

from .schemas import DebugPayload, DebugToolCall


@dataclass
class RequestDebugState:
    tool_calls: list[DebugToolCall] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    partial_data: bool = False

    def add_tool_call(
        self,
        *,
        tool_name: str,
        endpoint: str | None,
        duration_ms: int,
        retries: int,
        status: str,
        message: str | None = None,
    ) -> None:
        self.tool_calls.append(
            DebugToolCall(
                tool_name=tool_name,
                endpoint=endpoint,
                duration_ms=duration_ms,
                retries=retries,
                status="success" if status == "success" else "error",
                message=message,
            )
        )

    def add_note(self, note: str) -> None:
        if note and note not in self.notes:
            self.notes.append(note)

    def mark_partial(self) -> None:
        self.partial_data = True

    def to_payload(self) -> DebugPayload:
        return DebugPayload(tool_calls=self.tool_calls, notes=self.notes)


_debug_state_ctx: ContextVar[RequestDebugState | None] = ContextVar("debug_state_ctx", default=None)


def set_debug_state(state: RequestDebugState) -> Token:
    return _debug_state_ctx.set(state)


def reset_debug_state(token: Token) -> None:
    _debug_state_ctx.reset(token)


def get_debug_state() -> RequestDebugState | None:
    return _debug_state_ctx.get()

