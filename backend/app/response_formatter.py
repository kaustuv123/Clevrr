from __future__ import annotations

import json
import re
from typing import Any

from .schemas import ChatBlock, TableBlock, TextBlock


CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
JSON_CODE_BLOCK_RE = re.compile(r"```json\s*([\s\S]*?)```", re.IGNORECASE)


def _stringify_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text") or item.get("content")
                if text_value:
                    chunks.append(str(text_value))
            elif item:
                chunks.append(str(item))
        return "\n".join(chunks).strip()
    return str(content)


def _strip_code(text: str) -> str:
    cleaned = CODE_BLOCK_RE.sub("", text)
    return cleaned.strip()


def _extract_json_candidate(text: str) -> dict[str, Any] | None:
    for match in JSON_CODE_BLOCK_RE.finditer(text):
        candidate = match.group(1).strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict):
            return payload

    return None


def _coerce_blocks(payload_blocks: Any, fallback_text: str) -> list[ChatBlock]:
    blocks: list[ChatBlock] = []
    if isinstance(payload_blocks, list):
        for entry in payload_blocks:
            if not isinstance(entry, dict):
                continue
            block_type = entry.get("type")
            if block_type == "table":
                columns = entry.get("columns", [])
                rows = entry.get("rows", [])
                if isinstance(columns, list) and isinstance(rows, list):
                    columns = [str(column) for column in columns]
                    blocks.append(
                        TableBlock(
                            title=str(entry["title"]) if entry.get("title") is not None else None,
                            columns=columns,
                            rows=rows,
                        )
                    )
            elif block_type == "text":
                text_value = str(entry.get("text", "")).strip()
                if text_value:
                    blocks.append(TextBlock(text=_strip_code(text_value)))

    if not blocks:
        blocks.append(TextBlock(text=_strip_code(fallback_text)))
    return blocks


def format_agent_output(raw_content: Any) -> tuple[str, list[ChatBlock], list[str]]:
    text = _stringify_content(raw_content)
    text = text.strip()
    notes: list[str] = []

    payload = _extract_json_candidate(text)
    if payload is not None:
        answer = _strip_code(str(payload.get("answer", "")).strip())
        blocks = _coerce_blocks(payload.get("blocks"), fallback_text=answer or text)
        notes_payload = payload.get("notes")
        if isinstance(notes_payload, list):
            notes.extend(str(note) for note in notes_payload if note)
        if not answer:
            answer = _strip_code(text)
        return answer or "No answer generated.", blocks, notes

    cleaned_text = _strip_code(text)
    blocks = [TextBlock(text=cleaned_text or "No answer generated.")]
    return cleaned_text or "No answer generated.", blocks, notes

