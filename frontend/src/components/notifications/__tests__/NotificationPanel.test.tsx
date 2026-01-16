import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import NotificationPanel from "../NotificationPanel";
import { NotificationProvider } from "../../../contexts/NotificationContext";
import { AuthProvider } from "../../../contexts/AuthContext";
import { NotificationService } from "../../../services/notificationService";

// Mock the notification service
vi.mock("../../../services/notificationService");

const mockNotifications = [
  {
    id: 1,
    user_id: 1,
    task_id: "task1",
    message: "You have been assigned to task 'Test Task' by John Doe",
    type: "task_assigned" as const,
    is_read: false,
    created_at: "2024-01-01T10:00:00Z",
  },
  {
    id: 2,
    user_id: 1,
    task_id: "task2",
    message: "Task 'Another Task' status has been updated to 'in progress'",
    type: "task_updated" as const,
    is_read: true,
    created_at: "2024-01-01T09:00:00Z",
  },
];

const mockUser = {
  id: 1,
  email: "test@example.com",
  name: "Test User",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

// Mock AuthContext
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

// Mock the useAuth hook
vi.mock("../../../contexts/AuthContext", async () => {
  const actual = await vi.importActual("../../../contexts/AuthContext");
  return {
    ...actual,
    useAuth: () => ({
      user: mockUser,
      login: vi.fn(),
      logout: vi.fn(),
      loading: false,
    }),
  };
});

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <MockAuthProvider>
      <NotificationProvider>{component}</NotificationProvider>
    </MockAuthProvider>
  );
};

describe("NotificationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(NotificationService.getNotifications).mockResolvedValue(
      mockNotifications
    );
    vi.mocked(NotificationService.markAsRead).mockResolvedValue();
    vi.mocked(NotificationService.markAllAsRead).mockResolvedValue();
  });

  it("renders notification bell with unread count", async () => {
    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument(); // Unread count
    });
  });

  it("opens notification panel when bell is clicked", async () => {
    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument(); // Wait for unread count
    });

    fireEvent.click(screen.getByTitle("Notifications"));

    await waitFor(() => {
      expect(screen.getByText("Notifications")).toBeInTheDocument();
      expect(screen.getByText("Mark all as read")).toBeInTheDocument();
    });
  });

  it("displays notifications correctly", async () => {
    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Notifications"));

    await waitFor(() => {
      expect(
        screen.getByText(
          "You have been assigned to task 'Test Task' by John Doe"
        )
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Task 'Another Task' status has been updated to 'in progress'"
        )
      ).toBeInTheDocument();
    });
  });

  it("marks notification as read when clicked", async () => {
    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Notifications"));

    await waitFor(() => {
      expect(
        screen.getByText(
          "You have been assigned to task 'Test Task' by John Doe"
        )
      ).toBeInTheDocument();
    });

    // Click on the unread notification
    fireEvent.click(
      screen.getByText("You have been assigned to task 'Test Task' by John Doe")
    );

    await waitFor(() => {
      expect(NotificationService.markAsRead).toHaveBeenCalledWith(1);
    });
  });

  it("marks all notifications as read", async () => {
    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Notifications"));

    await waitFor(() => {
      expect(screen.getByText("Mark all as read")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Mark all as read"));

    await waitFor(() => {
      expect(NotificationService.markAllAsRead).toHaveBeenCalled();
    });
  });

  it("shows empty state when no notifications", async () => {
    vi.mocked(NotificationService.getNotifications).mockResolvedValue([]);

    renderWithProviders(<NotificationPanel />);

    await waitFor(() => {
      expect(screen.getByTitle("Notifications")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Notifications"));

    await waitFor(() => {
      expect(screen.getByText("No notifications")).toBeInTheDocument();
    });
  });
});
