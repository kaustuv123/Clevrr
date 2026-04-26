from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from langchain_core.tools import tool
from langchain_experimental.tools import PythonAstREPLTool
from pydantic import BaseModel, Field

from .debug import get_debug_state
from .security import unsafe_operation_message
from .shopify_client import (
    PaginatedResult,
    ShopifyAPIError,
    ShopifyClient,
    ShopifyClientError,
    ShopifyMalformedResponseError,
    ShopifyUnsafeMethodError,
)
from .time_windows import compute_time_windows


def _track_tool_call(
    *,
    tool_name: str,
    endpoint: str | None,
    duration_ms: int,
    retries: int = 0,
    status: str,
    message: str | None = None,
) -> None:
    debug_state = get_debug_state()
    if debug_state is None:
        return
    debug_state.add_tool_call(
        tool_name=tool_name,
        endpoint=endpoint,
        duration_ms=duration_ms,
        retries=retries,
        status=status,
        message=message,
    )


def _note_partial(result: PaginatedResult) -> None:
    if not result.partial_data:
        return
    debug_state = get_debug_state()
    if debug_state is None:
        return
    debug_state.mark_partial()
    debug_state.add_note("Pagination limit reached; response may include partial data.")


def _serialize_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, default=str)


class ShopifyToolInput(BaseModel):
    endpoint: str = Field(..., description="Shopify Admin REST endpoint, for example /orders.json")
    store_url: str = Field(..., description="Shopify store URL matching the configured store.")
    method: str = Field(default="GET", description="HTTP method. Must always be GET.")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters.")
    paginate: bool = Field(default=False, description="Whether to follow pagination links.")
    collection_key: str | None = Field(
        default=None,
        description="Collection key in the response (orders, products, customers) for paginated fetches.",
    )


class OrdersInput(BaseModel):
    store_url: str
    created_at_min: str | None = None
    created_at_max: str | None = None
    status: str = "any"
    limit: int = 250


class ProductsInput(BaseModel):
    store_url: str
    fields: str | None = "id,title,status,vendor,product_type,variants,created_at,updated_at"
    limit: int = 250


class CustomersInput(BaseModel):
    store_url: str
    fields: str | None = "id,created_at,first_name,last_name,orders_count,total_spent,last_order_id,email,default_address"
    limit: int = 250


class TimeWindowInput(BaseModel):
    store_url: str
    timezone: str | None = None


def build_tools(shopify_client: ShopifyClient) -> list[Any]:
    python_repl = PythonAstREPLTool()

    @tool(args_schema=ShopifyToolInput)
    async def get_shopify_data(
        endpoint: str,
        store_url: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        paginate: bool = False,
        collection_key: str | None = None,
    ) -> str:
        """Canonical Shopify data tool. Enforces GET-only API access."""
        started_at = perf_counter()
        retries = 0
        endpoint_for_trace = endpoint
        status = "success"
        trace_message: str | None = None
        try:
            if method.upper() != "GET":
                status = "error"
                trace_message = "Rejected unsafe method."
                message = unsafe_operation_message()
                return message

            if paginate:
                if not collection_key:
                    raise ShopifyClientError("collection_key is required when paginate=true.")
                result = await shopify_client.get_paginated_collection(
                    endpoint=endpoint,
                    collection_key=collection_key,
                    store_url=store_url,
                    params=params,
                )
                retries = result.total_retries
                _note_partial(result)
                return _serialize_json(
                    {
                        "items": result.items,
                        "meta": {
                            "partial_data": result.partial_data,
                            "pages_fetched": result.pages_fetched,
                            "retries": result.total_retries,
                        },
                    }
                )

            payload, retries = await shopify_client.get_json(
                endpoint=endpoint,
                store_url=store_url,
                params=params,
                method=method,
            )
            return _serialize_json({"data": payload, "meta": {"retries": retries}})
        except ShopifyUnsafeMethodError:
            status = "error"
            trace_message = "Rejected unsafe method."
            return unsafe_operation_message()
        except ShopifyMalformedResponseError as exc:
            status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        except ShopifyAPIError as exc:
            status = "error"
            trace_message = exc.detail
            return _serialize_json({"error": exc.detail, "status_code": exc.status_code})
        except ShopifyClientError as exc:
            status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="get_shopify_data",
                endpoint=endpoint_for_trace,
                duration_ms=duration_ms,
                retries=retries,
                status=status,
                message=trace_message,
            )

    @tool(args_schema=OrdersInput)
    async def get_orders_data(
        store_url: str,
        created_at_min: str | None = None,
        created_at_max: str | None = None,
        status: str = "any",
        limit: int = 250,
    ) -> str:
        """Fetch Shopify orders with pagination and retry handling."""
        started_at = perf_counter()
        retries = 0
        endpoint = "/orders.json"
        trace_status = "success"
        trace_message: str | None = None
        params: dict[str, Any] = {"status": status, "limit": min(max(limit, 1), 250)}
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max

        try:
            result = await shopify_client.get_paginated_collection(
                endpoint=endpoint,
                collection_key="orders",
                store_url=store_url,
                params=params,
            )
            retries = result.total_retries
            _note_partial(result)
            return _serialize_json(
                {
                    "orders": result.items,
                    "meta": {
                        "partial_data": result.partial_data,
                        "pages_fetched": result.pages_fetched,
                        "retries": result.total_retries,
                    },
                }
            )
        except ShopifyClientError as exc:
            trace_status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="get_orders_data",
                endpoint=endpoint,
                duration_ms=duration_ms,
                retries=retries,
                status=trace_status,
                message=trace_message,
            )

    @tool(args_schema=ProductsInput)
    async def get_products_data(
        store_url: str,
        fields: str | None = "id,title,status,vendor,product_type,variants,created_at,updated_at",
        limit: int = 250,
    ) -> str:
        """Fetch Shopify products with pagination and retry handling."""
        started_at = perf_counter()
        retries = 0
        endpoint = "/products.json"
        trace_status = "success"
        trace_message: str | None = None
        params: dict[str, Any] = {"limit": min(max(limit, 1), 250)}
        if fields:
            params["fields"] = fields
        try:
            result = await shopify_client.get_paginated_collection(
                endpoint=endpoint,
                collection_key="products",
                store_url=store_url,
                params=params,
            )
            retries = result.total_retries
            _note_partial(result)
            return _serialize_json(
                {
                    "products": result.items,
                    "meta": {
                        "partial_data": result.partial_data,
                        "pages_fetched": result.pages_fetched,
                        "retries": result.total_retries,
                    },
                }
            )
        except ShopifyClientError as exc:
            trace_status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="get_products_data",
                endpoint=endpoint,
                duration_ms=duration_ms,
                retries=retries,
                status=trace_status,
                message=trace_message,
            )

    @tool(args_schema=CustomersInput)
    async def get_customers_data(
        store_url: str,
        fields: str | None = "id,created_at,first_name,last_name,orders_count,total_spent,last_order_id,email,default_address",
        limit: int = 250,
    ) -> str:
        """Fetch Shopify customers with pagination and retry handling."""
        started_at = perf_counter()
        retries = 0
        endpoint = "/customers.json"
        trace_status = "success"
        trace_message: str | None = None
        params: dict[str, Any] = {"limit": min(max(limit, 1), 250)}
        if fields:
            params["fields"] = fields
        try:
            result = await shopify_client.get_paginated_collection(
                endpoint=endpoint,
                collection_key="customers",
                store_url=store_url,
                params=params,
            )
            retries = result.total_retries
            _note_partial(result)
            return _serialize_json(
                {
                    "customers": result.items,
                    "meta": {
                        "partial_data": result.partial_data,
                        "pages_fetched": result.pages_fetched,
                        "retries": result.total_retries,
                    },
                }
            )
        except ShopifyClientError as exc:
            trace_status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="get_customers_data",
                endpoint=endpoint,
                duration_ms=duration_ms,
                retries=retries,
                status=trace_status,
                message=trace_message,
            )

    @tool(args_schema=TimeWindowInput)
    async def get_time_windows(store_url: str, timezone: str | None = None) -> str:
        """Return timezone-aware UTC window boundaries for analytics queries."""
        started_at = perf_counter()
        endpoint = "/shop.json"
        retries = 0
        trace_status = "success"
        trace_message: str | None = None
        try:
            resolved_timezone = timezone or await shopify_client.get_shop_timezone(store_url=store_url)
            windows = compute_time_windows(resolved_timezone)
            return _serialize_json(
                {
                    "timezone": windows.timezone,
                    "now_utc": windows.now_utc,
                    "last_7_days_start_utc": windows.last_7_days_start_utc,
                    "month_start_utc": windows.month_start_utc,
                }
            )
        except ShopifyClientError as exc:
            trace_status = "error"
            trace_message = str(exc)
            return _serialize_json({"error": str(exc)})
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="get_time_windows",
                endpoint=endpoint,
                duration_ms=duration_ms,
                retries=retries,
                status=trace_status,
                message=trace_message,
            )

    @tool
    def python_repl_ast(code: str) -> str:
        """Run Python code for aggregation logic. Use only for analytics, not for external calls."""
        started_at = perf_counter()
        trace_status = "success"
        trace_message: str | None = None
        try:
            output = python_repl.run(code)
            return str(output)
        except Exception as exc:  # noqa: BLE001
            trace_status = "error"
            trace_message = str(exc)
            return f"Python analysis error: {exc}"
        finally:
            duration_ms = int((perf_counter() - started_at) * 1000)
            _track_tool_call(
                tool_name="python_repl_ast",
                endpoint=None,
                duration_ms=duration_ms,
                retries=0,
                status=trace_status,
                message=trace_message,
            )

    return [
        get_shopify_data,
        get_orders_data,
        get_products_data,
        get_customers_data,
        get_time_windows,
        python_repl_ast,
    ]
