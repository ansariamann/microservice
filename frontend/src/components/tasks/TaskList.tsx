import React, { useState, useEffect } from "react";
import { Task, TaskStatus } from "../../types/task";
import { taskService } from "../../services/taskService";
import { useAsync } from "../../hooks/useAsync";
import TaskItem from "./TaskItem";
import TaskForm from "./TaskForm";
import ErrorMessage from "../common/ErrorMessage";
import LoadingSpinner from "../common/LoadingSpinner";
import { PlusIcon, FunnelIcon } from "@heroicons/react/24/outline";

interface TaskListProps {
  userId?: string;
}

const TaskList: React.FC<TaskListProps> = ({ userId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [sortBy, setSortBy] = useState<"created_at" | "due_date" | "priority">(
    "created_at"
  );
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const {
    execute: loadTasks,
    loading,
    error,
  } = useAsync(async () => {
    const response = await taskService.getTasks();
    setTasks(response.data);
  });

  useEffect(() => {
    loadTasks();
  }, []);

  useEffect(() => {
    let filtered = [...tasks];

    // Apply status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((task) => task.status === statusFilter);
    }

    // Apply user filter if specified
    if (userId) {
      filtered = filtered.filter(
        (task) => task.created_by === userId || task.assigned_to === userId
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy];
      let bValue: any = b[sortBy];

      if (sortBy === "created_at" || sortBy === "due_date") {
        aValue = new Date(aValue || 0).getTime();
        bValue = new Date(bValue || 0).getTime();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredTasks(filtered);
  }, [tasks, statusFilter, sortBy, sortOrder, userId]);

  const handleTaskCreated = (newTask: Task) => {
    setTasks((prev) => [newTask, ...prev]);
    setShowCreateForm(false);
  };

  const handleTaskUpdated = (updatedTask: Task) => {
    setTasks((prev) =>
      prev.map((task) => (task.id === updatedTask.id ? updatedTask : task))
    );
    setEditingTask(null);
  };

  const handleTaskDeleted = (taskId: string) => {
    setTasks((prev) => prev.filter((task) => task.id !== taskId));
  };

  if (loading && tasks.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" text="Loading tasks..." />
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Error Message */}
      {error && (
        <ErrorMessage
          message={error}
          onDismiss={() => window.location.reload()}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Tasks</h2>
        <div className="flex flex-col sm:flex-row gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="sm:hidden inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filters
          </button>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">New Task</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>
      </div>

      {/* Filters and Sorting - Desktop */}
      <div className="hidden sm:flex flex-wrap gap-4 items-center bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center space-x-2">
          <label
            htmlFor="status-filter"
            className="text-sm font-medium text-gray-700 whitespace-nowrap"
          >
            Status:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as TaskStatus | "all")
            }
            className="border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 min-w-0"
          >
            <option value="all">All</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label
            htmlFor="sort-by"
            className="text-sm font-medium text-gray-700 whitespace-nowrap"
          >
            Sort by:
          </label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) =>
              setSortBy(
                e.target.value as "created_at" | "due_date" | "priority"
              )
            }
            className="border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 min-w-0"
          >
            <option value="created_at">Created Date</option>
            <option value="due_date">Due Date</option>
            <option value="priority">Priority</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label
            htmlFor="sort-order"
            className="text-sm font-medium text-gray-700 whitespace-nowrap"
          >
            Order:
          </label>
          <select
            id="sort-order"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
            className="border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 min-w-0"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Filters and Sorting - Mobile */}
      {showFilters && (
        <div className="sm:hidden bg-gray-50 p-4 rounded-lg space-y-4">
          <div>
            <label
              htmlFor="mobile-status-filter"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Status
            </label>
            <select
              id="mobile-status-filter"
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as TaskStatus | "all")
              }
              className="w-full border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All</option>
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="mobile-sort-by"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Sort by
            </label>
            <select
              id="mobile-sort-by"
              value={sortBy}
              onChange={(e) =>
                setSortBy(
                  e.target.value as "created_at" | "due_date" | "priority"
                )
              }
              className="w-full border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="created_at">Created Date</option>
              <option value="due_date">Due Date</option>
              <option value="priority">Priority</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="mobile-sort-order"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Order
            </label>
            <select
              id="mobile-sort-order"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
              className="w-full border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      )}

      {/* Task List */}
      <div className="space-y-4">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No tasks found</p>
            <p className="text-gray-400 text-sm mt-2">
              {statusFilter !== "all"
                ? "Try changing the filter"
                : "Create your first task to get started"}
            </p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onEdit={setEditingTask}
              onDelete={handleTaskDeleted}
              onUpdate={handleTaskUpdated}
            />
          ))
        )}
      </div>

      {/* Create Task Modal */}
      {showCreateForm && (
        <TaskForm
          onSubmit={handleTaskCreated}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Edit Task Modal */}
      {editingTask && (
        <TaskForm
          task={editingTask}
          onSubmit={handleTaskUpdated}
          onCancel={() => setEditingTask(null)}
        />
      )}
    </div>
  );
};

export default TaskList;
