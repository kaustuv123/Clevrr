import { render, screen } from "@testing-library/react";
import { App } from "../App";


describe("App", () => {
  it("renders chat UI controls", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Shopify Analyst Agent" })).toBeInTheDocument();
    expect(screen.getByLabelText("Ask a question")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });
});

