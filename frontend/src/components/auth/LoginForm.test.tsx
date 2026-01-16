import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import LoginForm from "./LoginForm";

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("LoginForm", () => {
  it("renders login form with all fields", () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<LoginForm onSubmit={mockOnSubmit} />);

    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
    expect(screen.getByLabelText("Email Address")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
    expect(screen.getByText("create a new account")).toBeInTheDocument();
  });

  it("shows validation errors for empty fields", async () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<LoginForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole("button", { name: "Sign In" });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Email is required")).toBeInTheDocument();
      expect(screen.getByText("Password is required")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows loading state when submitting", () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<LoginForm onSubmit={mockOnSubmit} isLoading={true} />);

    expect(screen.getByText("Signing In...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
  });

  it("displays error message when provided", () => {
    const mockOnSubmit = vi.fn();
    const errorMessage = "Invalid credentials";

    renderWithRouter(
      <LoginForm onSubmit={mockOnSubmit} error={errorMessage} />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
});
