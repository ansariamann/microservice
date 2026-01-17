import React, { useState, useEffect } from "react";
import {
  Task,
  TaskStatus,
  CreateTaskRequest,
  UpdateTaskRequest,
} from "../../types/task";
import { taskService } from "../../services/taskService";
import { useAsync } from "../../hooks/useAsync";
import ErrorMessage from "../common/ErrorMessage";
import LoadingSpinner from "../common/LoadingSpinner";
import GlassCard from "../common/GlassCard";
import AnimatedButton from "../common/AnimatedButton";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { motion } from "framer-motion";

interface TaskFormProps {
  task?: Task;
  onSubmit: (task: Task) => void;
  onCancel: () => void;
}

const TaskForm: React.FC<TaskFormProps> = ({ task, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    status: "todo" as TaskStatus,
    priority: "medium",
    due_date: "",
    assigned_to: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { execute: submitTask, loading } = useAsync(async () => {
    try {
      setErrors({});

      if (task) {
        // Update existing task
        const updateData: UpdateTaskRequest = {};
        if (formData.title !== task.title) updateData.title = formData.title;
        if (formData.description !== task.description)
          updateData.description = formData.description;
        if (formData.status !== task.status)
          updateData.status = formData.status;
        if (formData.priority !== task.priority)
          updateData.priority = formData.priority;
        if (formData.due_date !== (task.due_date || ""))
          updateData.due_date = formData.due_date || null;
        if (formData.assigned_to !== (task.assigned_to || ""))
          updateData.assigned_to = formData.assigned_to || null;

        const response = await taskService.updateTask(task.id, updateData);
        onSubmit(response.data);
      } else {
        // Create new task
        const createData: CreateTaskRequest = {
          title: formData.title,
          description: formData.description,
          status: formData.status,
          priority: formData.priority,
          due_date: formData.due_date || null,
          assigned_to: formData.assigned_to || null,
        };

        const response = await taskService.createTask(createData);
        onSubmit(response.data);
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === "string") {
          setErrors({ general: error.response.data.detail });
        } else if (Array.isArray(error.response.data.detail)) {
          const fieldErrors: Record<string, string> = {};
          error.response.data.detail.forEach((err: any) => {
            if (err.loc && err.msg) {
              const field = err.loc[err.loc.length - 1];
              fieldErrors[field] = err.msg;
            }
          });
          setErrors(fieldErrors);
        }
      } else {
        setErrors({ general: "An unexpected error occurred" });
      }
    }
  });

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        description: task.description || "",
        status: task.status,
        priority: task.priority || "medium",
        due_date: task.due_date ? task.due_date.split("T")[0] : "",
        assigned_to: task.assigned_to || "",
      });
    }
  }, [task]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Basic validation
    const newErrors: Record<string, string> = {};
    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    submitTask();
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const getInputClasses = (fieldName: string) => {
    const hasError = errors[fieldName];
    return `w-full bg-surface/50 border ${hasError ? "border-red-500/50 focus:ring-red-500" : "border-white/10 focus:ring-primary"
      } rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 transition-all duration-300 backdrop-blur-sm`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="w-full max-w-2xl"
      >
        <GlassCard className="w-full max-h-[90vh] overflow-y-auto" hoverEffect={false}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <h3 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              {task ? "Edit Task" : "Create New Task"}
            </h3>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-white transition-colors focus:outline-none p-1"
              aria-label="Close dialog"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* General Error */}
            {errors.general && <ErrorMessage message={errors.general} />}

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-1">
                Title *
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className={getInputClasses("title")}
                placeholder="Enter task title"
              />
              {errors.title && <p className="mt-1 text-sm text-red-400 ml-1">{errors.title}</p>}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                rows={4}
                value={formData.description}
                onChange={handleChange}
                className={getInputClasses("description")}
                placeholder="Enter task description"
              />
              {errors.description && <p className="mt-1 text-sm text-red-400 ml-1">{errors.description}</p>}
            </div>

            {/* Status and Priority Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-300 mb-1">
                  Status
                </label>
                <select
                  id="status"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className={getInputClasses("status")}
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                {errors.status && <p className="mt-1 text-sm text-red-400 ml-1">{errors.status}</p>}
              </div>

              <div>
                <label htmlFor="priority" className="block text-sm font-medium text-gray-300 mb-1">
                  Priority
                </label>
                <select
                  id="priority"
                  name="priority"
                  value={formData.priority}
                  onChange={handleChange}
                  className={getInputClasses("priority")}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
                {errors.priority && <p className="mt-1 text-sm text-red-400 ml-1">{errors.priority}</p>}
              </div>
            </div>

            {/* Due Date and Assigned To Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="due_date" className="block text-sm font-medium text-gray-300 mb-1">
                  Due Date
                </label>
                <input
                  type="date"
                  id="due_date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className={getInputClasses("due_date")}
                />
                {errors.due_date && <p className="mt-1 text-sm text-red-400 ml-1">{errors.due_date}</p>}
              </div>

              <div>
                <label htmlFor="assigned_to" className="block text-sm font-medium text-gray-300 mb-1">
                  Assigned To (User ID)
                </label>
                <input
                  type="text"
                  id="assigned_to"
                  name="assigned_to"
                  value={formData.assigned_to}
                  onChange={handleChange}
                  className={getInputClasses("assigned_to")}
                  placeholder="Enter user ID"
                />
                {errors.assigned_to && <p className="mt-1 text-sm text-red-400 ml-1">{errors.assigned_to}</p>}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-3 pt-6 border-t border-white/10">
              <AnimatedButton
                type="button"
                variant="ghost"
                onClick={onCancel}
              >
                Cancel
              </AnimatedButton>
              <AnimatedButton
                type="submit"
                variant="primary"
                isLoading={loading}
              >
                {task ? "Update Task" : "Create Task"}
              </AnimatedButton>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  );
};

export default TaskForm;
