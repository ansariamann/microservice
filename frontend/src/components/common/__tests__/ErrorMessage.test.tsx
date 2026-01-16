import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ErrorMessage from "../ErrorMessage";

describe("ErrorMessage", () => {
  it("renders error message with default variant", () => {
    render(<ErrorMessage message="Test error message" />);

    expect(screen.getByText("Test error message")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveClass(
      "bg-red-50",
      "border-red-200"
    );
  });

  it("renders warning variant correctly", () => {
    render(<ErrorMessage message="Warning message" variant="warning" />);

    expect(screen.getByText("Warning message")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveClass(
      "bg-yellow-50",
      "border-yellow-200"
    );
  });

  it("renders info variant correctly", () => {
    render(<ErrorMessage message="Info message" variant="info" />);

    expect(screen.getByText("Info message")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveClass(
      "bg-blue-50",
      "border-blue-200"
    );
  });

  it("calls onDismiss when dismiss button is clicked", () => {
    const mockOnDismiss = vi.fn();
    render(<ErrorMessage message="Test message" onDismiss={mockOnDismiss} />);

    const dismissButton = screen.getByRole("button", { name: "Dismiss" });
    fireEvent.click(dismissButton);

    expect(mockOnDismiss).toHaveBeenCalledTimes(1);
  });

  it("does not render dismiss button when onDismiss is not provided", () => {
    render(<ErrorMessage message="Test message" />);

    expect(
      screen.queryByRole("button", { name: "Dismiss" })
    ).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<ErrorMessage message="Test message" className="custom-class" />);

    expect(screen.getByRole("alert")).toHaveClass("custom-class");
  });
});
