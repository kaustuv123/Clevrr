from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .config import Settings
from .shopify_client import ShopifyClient
from .tools import build_tools


SYSTEM_PROMPT = """
You are a Shopify analytics assistant for business analysis.

Rules you must always follow:
1) Read-only mode only. Never perform or suggest POST, PUT, PATCH, DELETE.
2) If asked for a write operation, reply exactly: "This operation is not permitted."
3) Do not output raw code in the user-facing response.
4) Use tools to fetch and analyze data. Do not hallucinate numbers.
5) For date windows, use store timezone and prefer get_time_windows.
6) Keep responses concise and business-focused.

Current v1 scope to prioritize:
- Orders in last 7 days
- Top-selling products this month
- Repeat customers

Final response format (strict JSON object):
{
  "answer": "short business summary",
  "blocks": [
    {"type":"text","text":"brief context"},
    {"type":"table","title":"optional title","columns":["..."],"rows":[["..."]]}
  ],
  "notes": ["optional note"]
}
If no table is useful, return only a text block.
"""


@dataclass
class AgentService:
    settings: Settings

    def __post_init__(self) -> None:
        self.shopify_client = ShopifyClient(
            shop_name=self.settings.shopify_shop_name,
            api_version=self.settings.shopify_api_version,
            access_token=self.settings.shopify_access_token,
            timeout_seconds=self.settings.shopify_timeout_seconds,
            max_retries=self.settings.shopify_max_retries,
            backoff_seconds=self.settings.shopify_backoff_seconds,
            page_limit=self.settings.shopify_page_limit,
        )
        self.tools = build_tools(self.shopify_client)
        self.checkpointer = MemorySaver()
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.gemini_api_key,
            temperature=0.1,
        )
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer,
            prompt=SYSTEM_PROMPT,
        )

    async def run(self, *, question: str, session_id: str) -> Any:
        user_message = (
            f"Store URL: {self.shopify_client.shop_name}\n"
            f"User question: {question}\n"
            "Always include a concise answer and table block when useful."
        )
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": session_id}},
        )
        messages = result.get("messages", [])
        if not messages:
            return ""
        return messages[-1].content

    async def get_timezone(self) -> str:
        return await self.shopify_client.get_shop_timezone(store_url=self.shopify_client.shop_name)

