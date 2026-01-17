import React, { useState } from "react";
import { Task, TaskStatus } from "../../types/task";
import { taskService } from "../../services/taskService";
import { useAsync } from "../../hooks/useAsync";
import DeleteConfirmationDialog from "./DeleteConfirmationDialog";
import GlassCard from "../common/GlassCard";
import {
  PencilIcon,
  TrashIcon,
  CalendarIcon,
  UserIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

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
        return "bg-gray-500/20 text-gray-300 border-gray-500/30";
      case "in_progress":
        return "bg-blue-500/20 text-blue-300 border-blue-500/30 animate-pulse-slow";
      case "completed":
        return "bg-green-500/20 text-green-300 border-green-500/30";
      default:
        return "bg-gray-500/20 text-gray-300";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-400";
      case "medium":
        return "text-yellow-400";
      case "low":
        return "text-green-400";
      default:
        return "text-gray-400";
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
      <GlassCard className="p-6 transition-all duration-300" hoverEffect>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Title and Status */}
            <div className="flex items-center space-x-3 mb-3">
              <h3 className="text-lg font-semibold text-white truncate group-hover:text-primary transition-colors">
                {task.title}
              </h3>
              <span
                className={clsx(
                  "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
                  getStatusColor(task.status)
                )}
              >
                {task.status.replace("_", " ").toUpperCase()}
              </span>
              {task.priority && (
                <span
                  className={clsx(
                    "text-xs font-bold tracking-wider",
                    getPriorityColor(task.priority)
                  )}
                >
                  {task.priority.toUpperCase()}
                </span>
              )}
            </div>

            {/* Description */}
            {task.description && (
              <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                {task.description}
              </p>
            )}

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              {task.due_date && (
                <div
                  className={clsx(
                    "flex items-center space-x-1.5",
                    isOverdue(task.due_date) ? "text-red-400" : "text-gray-400"
                  )}
                >
                  <CalendarIcon className="h-4 w-4" />
                  <span>{formatDate(task.due_date)}</span>
                  {isOverdue(task.due_date) && (
                    <span className="text-red-400 font-medium ml-1">(Overdue)</span>
                  )}
                </div>
              )}

              {task.assigned_to && (
                <div className="flex items-center space-x-1.5 text-gray-400">
                  <UserIcon className="h-4 w-4" />
                  <span>Assigned: {task.assigned_to}</span>
                </div>
              )}

              <div className="flex items-center space-x-1.5 text-gray-400">
                <ClockIcon className="h-4 w-4" />
                <span>Created: {formatDate(task.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-3 ml-4">
            {/* Status Update Dropdown */}
            <select
              value={task.status}
              onChange={(e) => updateTaskStatus(e.target.value as TaskStatus)}
              disabled={isUpdatingStatus}
              className="text-sm bg-surface/50 border border-white/10 rounded-lg text-gray-300 focus:ring-primary focus:border-primary disabled:opacity-50 transition-colors cursor-pointer hover:bg-surface/80 px-3 py-1.5"
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>

            {/* Edit Button */}
            <button
              onClick={() => onEdit(task)}
              className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
              title="Edit task"
            >
              <PencilIcon className="h-4 w-4" />
            </button>

            {/* Delete Button */}
            <button
              onClick={() => setShowDeleteDialog(true)}
              className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/50"
              title="Delete task"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </GlassCard>

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
