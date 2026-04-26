import { FormEvent, useEffect, useMemo, useState } from "react";
import { sendChat } from "./api";
import type { ChatBlock, ChatResponse } from "./types";

type MessageItem = {
  id: string;
  role: "user" | "assistant";
  text: string;
  blocks?: ChatBlock[];
  meta?: ChatResponse["meta"];
  debug?: ChatResponse["debug"];
};

const SAMPLE_QUESTIONS = [
  "How many orders were placed in the last 7 days?",
  "Which products sold the most last month?",
  "Show a table of revenue by city.",
  "Who are my repeat customers?",
  "What is the AOV trend this month?",
  "Can you recommend what product to promote based on sales?"
];

const LOADING_STAGES = [
  "Reading Shopify context",
  "Fetching store data",
  "Running analysis",
  "Preparing the answer"
];

function renderBlock(block: ChatBlock, index: number) {
  if (block.type === "text") {
    return (
      <div className="text-block" key={`${block.type}-${index}`}>
        {block.text}
      </div>
    );
  }

  return (
    <div className="table-block" key={`${block.type}-${index}`}>
      {block.title ? <div className="table-title">{block.title}</div> : null}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {block.columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((value, valueIndex) => (
                  <td key={`${rowIndex}-${valueIndex}`}>{String(value ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function debugSummary(message: MessageItem): string | null {
  if (message.role !== "assistant" || !message.meta) return null;
  const partial = message.meta.partial_data ? "Partial data" : "Complete data";
  return `${message.meta.timezone} / ${message.meta.duration_ms}ms / ${partial}`;
}

function generateId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `id-${Math.random().toString(36).slice(2, 12)}`;
}

export function App() {
  const [prompt, setPrompt] = useState<string>("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [loadingIndex, setLoadingIndex] = useState<number>(0);
  const sessionId = useMemo(() => generateId(), []);

  useEffect(() => {
    if (!isLoading) {
      setLoadingIndex(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      setLoadingIndex((current) => (current + 1) % LOADING_STAGES.length);
    }, 1200);

    return () => window.clearInterval(intervalId);
  }, [isLoading]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt || isLoading) return;

    setError("");
    const userMessage: MessageItem = {
      id: generateId(),
      role: "user",
      text: trimmedPrompt
    };
    setMessages((current) => [...current, userMessage]);
    setPrompt("");
    setIsLoading(true);

    try {
      const result = await sendChat({
        message: trimmedPrompt,
        session_id: sessionId
      });
      const assistantMessage: MessageItem = {
        id: generateId(),
        role: "assistant",
        text: result.answer,
        blocks: result.blocks,
        meta: result.meta,
        debug: result.debug
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (submitError) {
      const typed = submitError as Error;
      setError(typed.message || "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <h1>Shopify Analyst</h1>
      </header>

      <main className="layout">
        <section className="chat-panel">
          <div className="sample-rail" aria-label="Sample questions">
            <div className="sample-grid">
              {SAMPLE_QUESTIONS.map((question) => (
                <button
                  className="sample-question"
                  key={question}
                  type="button"
                  onClick={() => setPrompt(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          <form className="input-form" onSubmit={onSubmit}>
            <label>
              Ask a question
              <textarea
                aria-label="Ask a question"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="How many orders did we get in the last 7 days?"
              />
            </label>
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Working" : "Send"}
            </button>
          </form>

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="messages" aria-live="polite">
            {!messages.length && !isLoading ? (
              <div className="empty-state">
                Ask a store question or choose a sample above to begin.
              </div>
            ) : null}

            {messages.map((message) => (
              <article key={message.id} className={`message ${message.role}`}>
                <div className="message-label">{message.role === "user" ? "You" : "Agent"}</div>
                <div className="message-text">{message.text}</div>
                {message.blocks?.map(renderBlock)}
                {message.meta ? <div className="message-meta">{debugSummary(message)}</div> : null}
              </article>
            ))}

            {isLoading ? (
              <article className="message assistant loading-message">
                <div className="message-label">Agent</div>
                <div className="loading-row">
                  <span className="loading-dots" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </span>
                  <span>{LOADING_STAGES[loadingIndex]}</span>
                </div>
                <div className="loading-bar" aria-hidden="true" />
              </article>
            ) : null}
          </div>
        </section>

        <aside className="debug-panel">
          <h2>Debug Trace</h2>
          <p>Latest sanitized execution details.</p>
          {messages
            .filter((message) => message.role === "assistant" && message.debug)
            .slice(-1)
            .map((message) => (
              <div className="debug-content" key={`${message.id}-debug`}>
                {message.debug?.tool_calls.length ? (
                  <ul>
                    {message.debug.tool_calls.map((call, idx) => (
                      <li key={`${call.tool_name}-${idx}`}>
                        <strong>{call.tool_name}</strong>
                        <div>endpoint: {call.endpoint || "n/a"}</div>
                        <div>
                          duration: {call.duration_ms}ms | retries: {call.retries} | status: {call.status}
                        </div>
                        {call.message ? <div>message: {call.message}</div> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div>No tool calls captured for this response.</div>
                )}
                {message.debug?.notes.length ? (
                  <>
                    <h3>Notes</h3>
                    <ul>
                      {message.debug.notes.map((note) => (
                        <li key={note}>{note}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
              </div>
            ))}
        </aside>
      </main>
    </div>
  );
}
