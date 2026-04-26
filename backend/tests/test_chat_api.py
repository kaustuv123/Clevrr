from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import ChatRequest
from app.security import unsafe_operation_message
from app.shopify_client import ShopifyClient


class FakeAgentService:
    def __init__(self) -> None:
        self.shopify_client = ShopifyClient(
            shop_name="clevrr-test.myshopify.com",
            api_version="2025-07",
            access_token="fake-token",
        )

    async def get_timezone(self) -> str:
        return "America/New_York"

    async def run(self, *, question: str, session_id: str) -> str:
        return '{"answer":"ok","blocks":[{"type":"text","text":"ok"}],"notes":[]}'


def build_client() -> TestClient:
    app = create_app()
    app.state.agent_service = FakeAgentService()
    return TestClient(app)


def test_chat_request_store_url_is_optional() -> None:
    request = ChatRequest(message="How many orders?", session_id="abc")
    assert request.store_url is None


def test_chat_works_when_store_url_is_omitted() -> None:
    client = build_client()
    response = client.post(
        "/api/chat",
        json={"message": "How many orders?", "session_id": "abc"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "ok"


def test_optional_store_url_is_validated_when_provided() -> None:
    client = build_client()
    response = client.post(
        "/api/chat",
        json={
            "message": "How many orders?",
            "session_id": "abc",
            "store_url": "wrong-store.myshopify.com",
        },
    )

    assert response.status_code == 400


def test_unsafe_request_keeps_exact_sentence() -> None:
    client = build_client()
    response = client.post(
        "/api/chat",
        json={"message": "Please delete an order", "session_id": "abc"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == unsafe_operation_message()

