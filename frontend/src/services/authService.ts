import apiClient from "./api";
import { UserLogin, UserRegistration, AuthResponse, User } from "../types/auth";

export class AuthService {
  /**
   * Register a new user
   */
  static async register(userData: UserRegistration): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>(
        "/api/v1/register",
        userData
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Registration failed"
      );
    }
  }

  /**
   * Login user
   */
  static async login(credentials: UserLogin): Promise<AuthResponse> {
    try {
      const response = await apiClient.post<AuthResponse>(
        "/api/v1/login",
        credentials
      );
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.error?.message || "Login failed");
    }
  }

  /**
   * Get current user profile
   */
  static async getProfile(): Promise<User> {
    try {
      const response = await apiClient.get<User>("/api/v1/profile");
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to fetch profile"
      );
    }
  }

  /**
   * Update user profile
   */
  static async updateProfile(profileData: {
    name: string;
    email: string;
  }): Promise<User> {
    try {
      const response = await apiClient.put<User>(
        "/api/v1/profile",
        profileData
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to update profile"
      );
    }
  }

  /**
   * Logout user (client-side cleanup)
   */
  static logout(): void {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated(): boolean {
    const token = localStorage.getItem("token");
    const user = localStorage.getItem("user");
    return !!(token && user);
  }

  /**
   * Get stored user data
   */
  static getStoredUser(): User | null {
    try {
      const userStr = localStorage.getItem("user");
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }

  /**
   * Get stored token
   */
  static getStoredToken(): string | null {
    return localStorage.getItem("token");
  }
}

export default AuthService;
