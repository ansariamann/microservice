import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import LoadingSpinner from "../LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders spinner with default props", () => {
    render(<LoadingSpinner />);

    const spinner = screen.getByRole("status", { hidden: true });
    expect(spinner).toHaveClass("h-6", "w-6", "border-blue-600");
  });

  it("renders spinner with small size", () => {
    render(<LoadingSpinner size="sm" />);

    const spinner = screen.getByRole("status", { hidden: true });
    expect(spinner).toHaveClass("h-4", "w-4");
  });

  it("renders spinner with large size", () => {
    render(<LoadingSpinner size="lg" />);

    const spinner = screen.getByRole("status", { hidden: true });
    expect(spinner).toHaveClass("h-8", "w-8");
  });

  it("renders spinner with white color", () => {
    render(<LoadingSpinner color="white" />);

    const spinner = screen.getByRole("status", { hidden: true });
    expect(spinner).toHaveClass("border-white");
  });

  it("renders spinner with text", () => {
    render(<LoadingSpinner text="Loading data..." />);

    expect(screen.getByText("Loading data...")).toBeInTheDocument();
    const container = screen.getByText("Loading data...").parentElement;
    expect(container).toHaveClass("flex", "items-center", "space-x-2");
  });

  it("applies custom className", () => {
    render(<LoadingSpinner className="custom-class" />);

    const spinner = screen.getByRole("status", { hidden: true });
    expect(spinner).toHaveClass("custom-class");
  });
});
