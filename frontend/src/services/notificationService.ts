import apiClient from "./api";
import { Notification } from "../types/notification";

export class NotificationService {
  /**
   * Get all notifications for the current user
   */
  static async getNotifications(): Promise<Notification[]> {
    try {
      const response = await apiClient.get<{
        notifications: Notification[];
        total: number;
      }>("/api/v1/notifications");
      return response.data.notifications;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to fetch notifications"
      );
    }
  }

  /**
   * Mark a notification as read
   */
  static async markAsRead(notificationId: number): Promise<void> {
    try {
      await apiClient.put(`/api/v1/notifications/${notificationId}/read`);
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message ||
          "Failed to mark notification as read"
      );
    }
  }

  /**
   * Mark all notifications as read
   */
  static async markAllAsRead(): Promise<void> {
    try {
      await apiClient.put("/api/v1/notifications/read-all");
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message ||
          "Failed to mark all notifications as read"
      );
    }
  }

  /**
   * Get unread notification count
   */
  static async getUnreadCount(): Promise<number> {
    try {
      const response = await apiClient.get<{ count: number }>(
        "/api/v1/notifications/unread-count"
      );
      return response.data.count;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to fetch unread count"
      );
    }
  }
}

// Export both named and default exports for compatibility
export const notificationService = NotificationService;
export default NotificationService;
