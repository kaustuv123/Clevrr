from app.security import is_unsafe_operation, unsafe_operation_message


def test_detects_unsafe_operations() -> None:
    assert is_unsafe_operation("Please delete this order")
    assert is_unsafe_operation("Can you update this customer?")


def test_allows_read_only_language() -> None:
    assert not is_unsafe_operation("How many orders did we get in the last 7 days?")


def test_unsafe_message_exact_text() -> None:
    assert unsafe_operation_message() == "This operation is not permitted."

