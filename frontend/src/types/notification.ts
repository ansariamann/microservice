export interface Notification {
  id: number;
  user_id: number;
  task_id: string;
  message: string;
  type: "task_assigned" | "task_updated";
  is_read: boolean;
  created_at: string;
}

export interface CreateNotificationRequest {
  user_id: number;
  task_id: string;
  message: string;
  type: "task_assigned" | "task_updated";
}
