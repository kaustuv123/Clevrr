from app.response_formatter import format_agent_output


def test_parses_json_payload() -> None:
    raw = """
    {
      "answer": "Orders are up this week.",
      "blocks": [
        {"type": "text", "text": "Weekly overview"},
        {"type": "table", "title": "Top Products", "columns": ["Product", "Units"], "rows": [["A", 5]]}
      ],
      "notes": ["Sample note"]
    }
    """
    answer, blocks, notes = format_agent_output(raw)

    assert answer == "Orders are up this week."
    assert len(blocks) == 2
    assert blocks[1].type == "table"
    assert notes == ["Sample note"]


def test_fallback_text_block_when_not_json() -> None:
    answer, blocks, notes = format_agent_output("Plain text answer")
    assert answer == "Plain text answer"
    assert len(blocks) == 1
    assert blocks[0].type == "text"
    assert notes == []

