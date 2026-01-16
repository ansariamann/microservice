export interface Task {
  id: string;
  title: string;
  description: string;
  due_date: string;
  status: "to_do" | "in_progress" | "done";
  creator_id: number;
  assignee_id: number;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description: string;
  due_date: string;
  assignee_id?: number;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  due_date?: string;
  status?: "to_do" | "in_progress" | "done";
  assignee_id?: number;
}
