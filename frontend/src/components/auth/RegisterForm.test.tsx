import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { BrowserRouter } from "react-router-dom";
import RegisterForm from "./RegisterForm";

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("RegisterForm", () => {
  it("renders registration form with all fields", () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<RegisterForm onSubmit={mockOnSubmit} />);

    expect(screen.getByText("Create your account")).toBeInTheDocument();
    expect(screen.getByLabelText("Full Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email Address")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create Account" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("sign in to your existing account")
    ).toBeInTheDocument();
  });

  it("shows validation errors for empty fields", async () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<RegisterForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole("button", { name: "Create Account" });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Name is required")).toBeInTheDocument();
      expect(screen.getByText("Email is required")).toBeInTheDocument();
      expect(screen.getByText("Password is required")).toBeInTheDocument();
      expect(
        screen.getByText("Please confirm your password")
      ).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows loading state when submitting", () => {
    const mockOnSubmit = vi.fn();

    renderWithRouter(<RegisterForm onSubmit={mockOnSubmit} isLoading={true} />);

    expect(screen.getByText("Creating Account...")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /creating account/i })
    ).toBeDisabled();
  });

  it("displays error message when provided", () => {
    const mockOnSubmit = vi.fn();
    const errorMessage = "Registration failed";

    renderWithRouter(
      <RegisterForm onSubmit={mockOnSubmit} error={errorMessage} />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
});
