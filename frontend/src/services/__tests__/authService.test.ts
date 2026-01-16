import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import AuthService from "../authService";
import { UserLogin, UserRegistration } from "../../types/auth";

// Mock axios
vi.mock("axios");
const mockedAxios = vi.mocked(axios);

// Mock the API client
vi.mock("../api", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
  },
}));

import apiClient from "../api";
const mockedApiClient = vi.mocked(apiClient);

describe("AuthService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("register", () => {
    it("should register a user successfully", async () => {
      const userData: UserRegistration = {
        name: "John Doe",
        email: "john@example.com",
        password: "password123",
      };

      const mockResponse = {
        data: {
          access_token: "test-token",
          token_type: "bearer",
          user: {
            id: 1,
            name: "John Doe",
            email: "john@example.com",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z",
          },
        },
      };

      mockedApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.register(userData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        "/api/v1/register",
        userData
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("should throw error on registration failure", async () => {
      const userData: UserRegistration = {
        name: "John Doe",
        email: "john@example.com",
        password: "password123",
      };

      const mockError = {
        response: {
          data: {
            error: {
              message: "Email already exists",
            },
          },
        },
      };

      mockedApiClient.post.mockRejectedValueOnce(mockError);

      await expect(AuthService.register(userData)).rejects.toThrow(
        "Email already exists"
      );
    });
  });

  describe("login", () => {
    it("should login a user successfully", async () => {
      const credentials: UserLogin = {
        email: "john@example.com",
        password: "password123",
      };

      const mockResponse = {
        data: {
          access_token: "test-token",
          token_type: "bearer",
          user: {
            id: 1,
            name: "John Doe",
            email: "john@example.com",
            created_at: "2023-01-01T00:00:00Z",
            updated_at: "2023-01-01T00:00:00Z",
          },
        },
      };

      mockedApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.login(credentials);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        "/api/v1/login",
        credentials
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("should throw error on login failure", async () => {
      const credentials: UserLogin = {
        email: "john@example.com",
        password: "wrongpassword",
      };

      const mockError = {
        response: {
          data: {
            error: {
              message: "Invalid credentials",
            },
          },
        },
      };

      mockedApiClient.post.mockRejectedValueOnce(mockError);

      await expect(AuthService.login(credentials)).rejects.toThrow(
        "Invalid credentials"
      );
    });
  });

  describe("getProfile", () => {
    it("should get user profile successfully", async () => {
      const mockUser = {
        id: 1,
        name: "John Doe",
        email: "john@example.com",
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      };

      const mockResponse = { data: mockUser };
      mockedApiClient.get.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.getProfile();

      expect(mockedApiClient.get).toHaveBeenCalledWith("/api/v1/profile");
      expect(result).toEqual(mockUser);
    });
  });

  describe("updateProfile", () => {
    it("should update user profile successfully", async () => {
      const profileData = {
        name: "Jane Doe",
        email: "jane@example.com",
      };

      const mockUpdatedUser = {
        id: 1,
        name: "Jane Doe",
        email: "jane@example.com",
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-02T00:00:00Z",
      };

      const mockResponse = { data: mockUpdatedUser };
      mockedApiClient.put.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.updateProfile(profileData);

      expect(mockedApiClient.put).toHaveBeenCalledWith(
        "/api/v1/profile",
        profileData
      );
      expect(result).toEqual(mockUpdatedUser);
    });
  });

  describe("logout", () => {
    it("should clear localStorage on logout", () => {
      localStorage.setItem("token", "test-token");
      localStorage.setItem("user", JSON.stringify({ id: 1, name: "John" }));

      AuthService.logout();

      expect(localStorage.getItem("token")).toBeNull();
      expect(localStorage.getItem("user")).toBeNull();
    });
  });

  describe("isAuthenticated", () => {
    it("should return true when token and user exist", () => {
      localStorage.setItem("token", "test-token");
      localStorage.setItem("user", JSON.stringify({ id: 1, name: "John" }));

      expect(AuthService.isAuthenticated()).toBe(true);
    });

    it("should return false when token or user is missing", () => {
      localStorage.setItem("token", "test-token");
      // No user in localStorage

      expect(AuthService.isAuthenticated()).toBe(false);
    });
  });

  describe("getStoredUser", () => {
    it("should return parsed user from localStorage", () => {
      const user = { id: 1, name: "John", email: "john@example.com" };
      localStorage.setItem("user", JSON.stringify(user));

      const result = AuthService.getStoredUser();

      expect(result).toEqual(user);
    });

    it("should return null for invalid JSON", () => {
      localStorage.setItem("user", "invalid-json");

      const result = AuthService.getStoredUser();

      expect(result).toBeNull();
    });

    it("should return null when no user in localStorage", () => {
      const result = AuthService.getStoredUser();

      expect(result).toBeNull();
    });
  });
});
