import asyncio

import httpx
import pytest
import respx

from app.shopify_client import (
    ShopifyClient,
    ShopifyMalformedResponseError,
    ShopifyUnsafeMethodError,
)


def build_client(page_limit: int = 2, max_retries: int = 2) -> ShopifyClient:
    return ShopifyClient(
        shop_name="clevrr-test.myshopify.com",
        api_version="2025-07",
        access_token="fake-token",
        page_limit=page_limit,
        max_retries=max_retries,
        backoff_seconds=0.0,
    )


@pytest.mark.asyncio
async def test_get_only_enforced() -> None:
    client = build_client()
    with pytest.raises(ShopifyUnsafeMethodError):
        await client.get_json(
            endpoint="/orders.json",
            store_url="clevrr-test.myshopify.com",
            method="POST",
        )


@pytest.mark.asyncio
async def test_429_retries_then_success() -> None:
    client = build_client(max_retries=2)
    url = "https://clevrr-test.myshopify.com/admin/api/2025-07/orders.json"

    with respx.mock(assert_all_called=True) as mock:
        mock.get(url).side_effect = [
            httpx.Response(429, json={"error": "rate limit"}),
            httpx.Response(200, json={"orders": []}),
        ]
        payload, retries = await client.get_json(
            endpoint="/orders.json",
            store_url="clevrr-test.myshopify.com",
        )

    assert payload == {"orders": []}
    assert retries == 1


@pytest.mark.asyncio
async def test_pagination_cap_marks_partial_data() -> None:
    client = build_client(page_limit=1)
    first_url = "https://clevrr-test.myshopify.com/admin/api/2025-07/orders.json"
    next_url = "https://clevrr-test.myshopify.com/admin/api/2025-07/orders.json?page_info=abc"
    link_header = f'<{next_url}>; rel="next"'

    with respx.mock(assert_all_called=True) as mock:
        mock.get(first_url).respond(
            200,
            json={"orders": [{"id": 1}]},
            headers={"Link": link_header},
        )
        result = await client.get_paginated_collection(
            endpoint="/orders.json",
            collection_key="orders",
            store_url="clevrr-test.myshopify.com",
        )

    assert result.items == [{"id": 1}]
    assert result.partial_data is True
    assert result.pages_fetched == 1


@pytest.mark.asyncio
async def test_malformed_response_raises() -> None:
    client = build_client()
    url = "https://clevrr-test.myshopify.com/admin/api/2025-07/orders.json"

    with respx.mock(assert_all_called=True) as mock:
        mock.get(url).respond(200, text="not-json")
        with pytest.raises(ShopifyMalformedResponseError):
            await client.get_json(
                endpoint="/orders.json",
                store_url="clevrr-test.myshopify.com",
            )

