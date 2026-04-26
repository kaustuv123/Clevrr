import type { ChatRequest, ChatResponse } from "./types";

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // ignore JSON parse failures for error payload
    }
    throw new Error(detail);
  }

  return (await response.json()) as ChatResponse;
}

