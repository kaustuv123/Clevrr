export type TextBlock = {
  type: "text";
  text: string;
};

export type TableBlock = {
  type: "table";
  title?: string | null;
  columns: string[];
  rows: Array<Array<string | number | boolean | null>>;
};

export type ChatBlock = TextBlock | TableBlock;

export type ChatMeta = {
  timezone: string;
  partial_data: boolean;
  duration_ms: number;
  session_id: string;
};

export type DebugToolCall = {
  tool_name: string;
  endpoint?: string | null;
  duration_ms: number;
  retries: number;
  status: "success" | "error";
  message?: string | null;
};

export type DebugPayload = {
  tool_calls: DebugToolCall[];
  notes: string[];
};

export type ChatResponse = {
  answer: string;
  blocks: ChatBlock[];
  meta: ChatMeta;
  debug: DebugPayload;
};

export type ChatRequest = {
  message: string;
  session_id: string;
};

