import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders without crashing", () => {
    render(<App />);
    // Since the app redirects to login when not authenticated,
    // we should see the login page
    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
  });
});
