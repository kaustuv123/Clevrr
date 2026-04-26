from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question to the Shopify analysis agent.")
    session_id: str = Field(..., min_length=1, description="Session identifier used for per-session memory.")


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    title: str | None = None
    columns: list[str]
    rows: list[list[Any]]


ChatBlock = TextBlock | TableBlock


class ResponseMeta(BaseModel):
    timezone: str
    partial_data: bool
    duration_ms: int
    session_id: str


class DebugToolCall(BaseModel):
    tool_name: str
    endpoint: str | None = None
    duration_ms: int
    retries: int = 0
    status: Literal["success", "error"]
    message: str | None = None


class DebugPayload(BaseModel):
    tool_calls: list[DebugToolCall] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    blocks: list[ChatBlock]
    meta: ResponseMeta
    debug: DebugPayload

