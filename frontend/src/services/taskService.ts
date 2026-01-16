import apiClient from "./api";
import { Task, TaskCreate, TaskUpdate } from "../types/task";

export class TaskService {
  /**
   * Get all tasks for the current user
   */
  static async getTasks(): Promise<Task[]> {
    try {
      const response = await apiClient.get<Task[]>("/api/v1/tasks");
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to fetch tasks"
      );
    }
  }

  /**
   * Get a specific task by ID
   */
  static async getTask(taskId: string): Promise<Task> {
    try {
      const response = await apiClient.get<Task>(`/api/v1/tasks/${taskId}`);
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to fetch task"
      );
    }
  }

  /**
   * Create a new task
   */
  static async createTask(taskData: TaskCreate): Promise<Task> {
    try {
      const response = await apiClient.post<Task>("/api/v1/tasks", taskData);
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to create task"
      );
    }
  }

  /**
   * Update an existing task
   */
  static async updateTask(taskId: string, taskData: TaskUpdate): Promise<Task> {
    try {
      const response = await apiClient.put<Task>(
        `/api/v1/tasks/${taskId}`,
        taskData
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to update task"
      );
    }
  }

  /**
   * Delete a task
   */
  static async deleteTask(taskId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/tasks/${taskId}`);
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to delete task"
      );
    }
  }

  /**
   * Assign a task to a user
   */
  static async assignTask(taskId: string, assigneeId: number): Promise<Task> {
    try {
      const response = await apiClient.put<Task>(`/api/v1/tasks/${taskId}`, {
        assignee_id: assigneeId,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to assign task"
      );
    }
  }

  /**
   * Update task status
   */
  static async updateTaskStatus(
    taskId: string,
    status: "to_do" | "in_progress" | "done"
  ): Promise<Task> {
    try {
      const response = await apiClient.put<Task>(`/api/v1/tasks/${taskId}`, {
        status,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.error?.message || "Failed to update task status"
      );
    }
  }
}

// Export both named and default exports for compatibility
export const taskService = TaskService;
export default TaskService;
