from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


NEXT_LINK_RE = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


class ShopifyClientError(Exception):
    pass


class ShopifyValidationError(ShopifyClientError):
    pass


class ShopifyUnsafeMethodError(ShopifyClientError):
    pass


class ShopifyAPIError(ShopifyClientError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ShopifyMalformedResponseError(ShopifyClientError):
    pass


@dataclass
class PaginatedResult:
    items: list[dict[str, Any]]
    partial_data: bool
    pages_fetched: int
    total_retries: int


class ShopifyClient:
    def __init__(
        self,
        *,
        shop_name: str,
        api_version: str,
        access_token: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
        page_limit: int = 4,
    ):
        self.shop_name = shop_name.strip().strip("\"'").lower()
        self.api_version = api_version.strip().strip("\"'")
        self.access_token = access_token.strip().strip("\"'")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.page_limit = page_limit
        self._timezone_cache: dict[str, str] = {}

    def validate_store_url(self, store_url: str) -> str:
        candidate = store_url.strip().strip("\"'")
        if not candidate:
            raise ShopifyValidationError("Store URL is required.")
        if "://" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower().strip()
        if not host:
            raise ShopifyValidationError("Store URL is invalid.")
        if host != self.shop_name:
            raise ShopifyValidationError(
                f"Store URL host '{host}' does not match configured store '{self.shop_name}'."
            )
        return host

    def _base_url_for_host(self, store_host: str) -> str:
        return f"https://{store_host}/admin/api/{self.api_version}"

    @staticmethod
    def _extract_next_link(link_header: str | None) -> str | None:
        if not link_header:
            return None
        match = NEXT_LINK_RE.search(link_header)
        if not match:
            return None
        return match.group(1)

    async def _request_json_url(
        self,
        *,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], httpx.Headers, int]:
        retries = 0
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Accept": "application/json",
        }

        for attempt in range(self.max_retries + 1):
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=headers, params=params)

            if response.status_code == 429 and attempt < self.max_retries:
                retries += 1
                await asyncio.sleep(self.backoff_seconds * (2**attempt))
                continue

            if response.status_code >= 400:
                raise ShopifyAPIError(
                    status_code=response.status_code,
                    detail=f"Shopify request failed with status {response.status_code}.",
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise ShopifyMalformedResponseError("Shopify response is not valid JSON.") from exc
            if not isinstance(payload, dict):
                raise ShopifyMalformedResponseError("Shopify response JSON must be an object.")

            return payload, response.headers, retries

        raise ShopifyAPIError(status_code=429, detail="Shopify rate limit retries exhausted.")

    async def get_json(
        self,
        *,
        endpoint: str,
        store_url: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> tuple[dict[str, Any], int]:
        if method.upper() != "GET":
            raise ShopifyUnsafeMethodError("Only GET requests are permitted.")
        store_host = self.validate_store_url(store_url)

        normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self._base_url_for_host(store_host)}{normalized_endpoint}"
        payload, _, retries = await self._request_json_url(url=url, params=params)
        return payload, retries

    async def get_paginated_collection(
        self,
        *,
        endpoint: str,
        collection_key: str,
        store_url: str,
        params: dict[str, Any] | None = None,
        page_limit: int | None = None,
    ) -> PaginatedResult:
        store_host = self.validate_store_url(store_url)
        normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self._base_url_for_host(store_host)}{normalized_endpoint}"

        effective_params = dict(params or {})
        effective_params.setdefault("limit", 250)

        pages_limit = page_limit or self.page_limit
        pages_fetched = 0
        total_retries = 0
        partial_data = False
        all_items: list[dict[str, Any]] = []
        next_url: str | None = url
        current_params = effective_params

        while next_url:
            if pages_fetched >= pages_limit:
                partial_data = True
                break

            parsed_next = urlparse(next_url)
            if parsed_next.hostname and parsed_next.hostname.lower() != store_host:
                raise ShopifyValidationError("Pagination URL host mismatch.")

            payload, headers, retries = await self._request_json_url(url=next_url, params=current_params)
            total_retries += retries

            items = payload.get(collection_key)
            if not isinstance(items, list):
                raise ShopifyMalformedResponseError(
                    f"Expected a list under key '{collection_key}' in Shopify response."
                )
            all_items.extend(items)
            pages_fetched += 1

            next_url = self._extract_next_link(headers.get("Link"))
            current_params = None

        if next_url:
            partial_data = True

        return PaginatedResult(
            items=all_items,
            partial_data=partial_data,
            pages_fetched=pages_fetched,
            total_retries=total_retries,
        )

    async def get_shop_timezone(self, *, store_url: str) -> str:
        store_host = self.validate_store_url(store_url)
        if store_host in self._timezone_cache:
            return self._timezone_cache[store_host]

        payload, _ = await self.get_json(endpoint="/shop.json", store_url=store_host)
        shop = payload.get("shop", {})
        timezone_name = (
            shop.get("iana_timezone")
            or shop.get("timezone")
            or "UTC"
        )
        if not isinstance(timezone_name, str):
            timezone_name = "UTC"
        self._timezone_cache[store_host] = timezone_name
        return timezone_name
