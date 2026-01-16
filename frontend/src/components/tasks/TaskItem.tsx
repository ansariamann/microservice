import React, { useState } from "react";
import { Task, TaskStatus } from "../../types/task";
import { taskService } from "../../services/taskService";
import { useAsync } from "../../hooks/useAsync";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import {
  PencilIcon,
  TrashIcon,
  CalendarIcon,
  UserIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

interface TaskItemProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onUpdate: (task: Task) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({
  task,
  onEdit,
  onDelete,
  onUpdate,
}) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  const { execute: updateTaskStatus } = useAsync(
    async (newStatus: TaskStatus) => {
      setIsUpdatingStatus(true);
      try {
        const response = await taskService.updateTask(task.id, {
          status: newStatus,
        });
        onUpdate(response.data);
      } finally {
        setIsUpdatingStatus(false);
      }
    }
  );

  const { execute: deleteTask } = useAsync(async () => {
    await taskService.deleteTask(task.id);
    onDelete(task.id);
    setShowDeleteDialog(false);
  });

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case "todo":
        return "bg-gray-100 text-gray-800";
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "completed":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-600";
      case "medium":
        return "text-yellow-600";
      case "low":
        return "text-green-600";
      default:
        return "text-gray-600";
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No due date";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const isOverdue = (dueDateString: string | null) => {
    if (!dueDateString) return false;
    const dueDate = new Date(dueDateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return dueDate < today && task.status !== "completed";
  };

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Title and Status */}
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-medium text-gray-900 truncate">
                {task.title}
              </h3>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                  task.status
                )}`}
              >
                {task.status.replace("_", " ").toUpperCase()}
              </span>
              {task.priority && (
                <span
                  className={`text-xs font-medium ${getPriorityColor(
                    task.priority
                  )}`}
                >
                  {task.priority.toUpperCase()} PRIORITY
                </span>
              )}
            </div>

            {/* Description */}
            {task.description && (
              <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                {task.description}
              </p>
            )}

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              {task.due_date && (
                <div
                  className={`flex items-center space-x-1 ${
                    isOverdue(task.due_date) ? "text-red-600" : ""
                  }`}
                >
                  <CalendarIcon className="h-4 w-4" />
                  <span>{formatDate(task.due_date)}</span>
                  {isOverdue(task.due_date) && (
                    <span className="text-red-600 font-medium">(Overdue)</span>
                  )}
                </div>
              )}

              {task.assigned_to && (
                <div className="flex items-center space-x-1">
                  <UserIcon className="h-4 w-4" />
                  <span>Assigned to: {task.assigned_to}</span>
                </div>
              )}

              <div className="flex items-center space-x-1">
                <ClockIcon className="h-4 w-4" />
                <span>Created: {formatDate(task.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 ml-4">
            {/* Status Update Dropdown */}
            <select
              value={task.status}
              onChange={(e) => updateTaskStatus(e.target.value as TaskStatus)}
              disabled={isUpdatingStatus}
              className="text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>

            {/* Edit Button */}
            <button
              onClick={() => onEdit(task)}
              className="p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-md"
              title="Edit task"
            >
              <PencilIcon className="h-4 w-4" />
            </button>

            {/* Delete Button */}
            <button
              onClick={() => setShowDeleteDialog(true)}
              className="p-2 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 rounded-md"
              title="Delete task"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <DeleteConfirmationDialog
          taskTitle={task.title}
          onConfirm={deleteTask}
          onCancel={() => setShowDeleteDialog(false)}
        />
      )}
    </>
  );
};

export default TaskItem;
