from __future__ import annotations

import re


UNSAFE_OPERATION_PATTERN = re.compile(
    r"\b("
    r"post|put|patch|delete|remove|destroy|erase|create|insert|update|edit|modify|cancel|refund|fulfill"
    r")\b",
    re.IGNORECASE,
)


def is_unsafe_operation(message: str) -> bool:
    """Detect requests that imply write operations."""
    return bool(UNSAFE_OPERATION_PATTERN.search(message))


def unsafe_operation_message() -> str:
    return "This operation is not permitted."

