import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "../App";
import { sendChat } from "../api";

vi.mock("../api", () => ({
  sendChat: vi.fn()
}));


describe("App", () => {
  beforeEach(() => {
    vi.mocked(sendChat).mockReset();
  });

  it("renders chat UI controls", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Shopify Analyst" })).toBeInTheDocument();
    expect(screen.getByLabelText("Ask a question")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
    expect(screen.queryByText(/interview/i)).not.toBeInTheDocument();
  });

  it("fills the prompt when a sample question is clicked", () => {
    render(<App />);
    fireEvent.click(screen.getAllByRole("button", { name: "Who are my repeat customers?" })[0]);
    expect(screen.getByLabelText("Ask a question")).toHaveValue("Who are my repeat customers?");
  });

  it("shows loading state while the request is pending", async () => {
    vi.mocked(sendChat).mockImplementation(() => new Promise(() => undefined));
    render(<App />);

    fireEvent.change(screen.getByLabelText("Ask a question"), {
      target: { value: "How many orders were placed in the last 7 days?" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Reading Shopify context")).toBeInTheDocument();
  });

  it("renders assistant text and table blocks", async () => {
    vi.mocked(sendChat).mockResolvedValue({
      answer: "Top product is Wireless Mouse.",
      blocks: [
        { type: "text", text: "Here is the product summary." },
        {
          type: "table",
          title: "Top products",
          columns: ["Product", "Units"],
          rows: [["Wireless Mouse", 12]]
        }
      ],
      meta: {
        timezone: "America/New_York",
        partial_data: false,
        duration_ms: 123,
        session_id: "session"
      },
      debug: { tool_calls: [], notes: [] }
    });

    render(<App />);
    fireEvent.change(screen.getByLabelText("Ask a question"), {
      target: { value: "Which products sold the most last month?" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(screen.getByText("Top product is Wireless Mouse.")).toBeInTheDocument());
    expect(screen.getByText("Top products")).toBeInTheDocument();
    expect(screen.getByText("Wireless Mouse")).toBeInTheDocument();
  });
});
