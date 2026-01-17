import React, { useState, useEffect } from "react";
import { Task, TaskStatus } from "../../types/task";
import { taskService } from "../../services/taskService";
import { useAsync } from "../../hooks/useAsync";
import TaskItem from "./TaskItem";
import TaskForm from "./TaskForm";
import ErrorMessage from "../common/ErrorMessage";
import LoadingSpinner from "../common/LoadingSpinner";
import AnimatedButton from "../common/AnimatedButton";
import GlassCard from "../common/GlassCard";
import { PlusIcon, FunnelIcon, AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";

interface TaskListProps {
  userId?: string;
}

const TaskList: React.FC<TaskListProps> = ({ userId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [sortBy, setSortBy] = useState<"created_at" | "due_date" | "priority">("created_at");
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

    if (statusFilter !== "all") {
      filtered = filtered.filter((task) => task.status === statusFilter);
    }

    if (userId) {
      filtered = filtered.filter(
        (task) => task.created_by === userId || task.assigned_to === userId
      );
    }

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

  const FilterControls = () => (
    <div className="flex flex-wrap gap-4 items-center">
      <div className="flex items-center space-x-2">
        <label htmlFor="status-filter" className="text-sm font-medium text-gray-400">Status:</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "all")}
          className="bg-surface/50 border border-white/10 rounded-lg text-sm text-gray-200 focus:ring-primary focus:border-primary px-3 py-1.5"
        >
          <option value="all">All</option>
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <label htmlFor="sort-by" className="text-sm font-medium text-gray-400">Sort:</label>
        <select
          id="sort-by"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "created_at" | "due_date" | "priority")}
          className="bg-surface/50 border border-white/10 rounded-lg text-sm text-gray-200 focus:ring-primary focus:border-primary px-3 py-1.5"
        >
          <option value="created_at">Created</option>
          <option value="due_date">Due Date</option>
          <option value="priority">Priority</option>
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <select
          id="sort-order"
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
          className="bg-surface/50 border border-white/10 rounded-lg text-sm text-gray-200 focus:ring-primary focus:border-primary px-3 py-1.5"
        >
          <option value="desc">Newest</option>
          <option value="asc">Oldest</option>
        </select>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {error && <ErrorMessage message={error} onDismiss={() => window.location.reload()} />}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
          Tasks
        </h2>
        <div className="flex gap-3">
          <AnimatedButton
            onClick={() => setShowFilters(!showFilters)}
            variant="outline"
            className="sm:hidden"
          >
            <FunnelIcon className="h-5 w-5 mr-2" />
            Filters
          </AnimatedButton>
          <AnimatedButton onClick={() => setShowCreateForm(true)}>
            <PlusIcon className="h-5 w-5 mr-2" />
            New Task
          </AnimatedButton>
        </div>
      </div>

      {/* Desktop Filters */}
      <GlassCard className="hidden sm:block p-4" hoverEffect={false}>
        <div className="flex items-center gap-2 mb-2 text-primary font-medium">
          <AdjustmentsHorizontalIcon className="w-5 h-5" />
          <span>Filter & Sort</span>
        </div>
        <FilterControls />
      </GlassCard>

      {/* Mobile Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="sm:hidden"
          >
            <GlassCard className="p-4 space-y-4">
              <FilterControls />
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Task List */}
      <motion.div
        layout
        className="space-y-4"
      >
        <AnimatePresence mode="popLayout">
          {filteredTasks.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <GlassCard className="inline-block p-8" hoverEffect={false}>
                <p className="text-gray-400 text-lg">No tasks found</p>
                <p className="text-gray-500 text-sm mt-2">
                  {statusFilter !== "all" ? "Try changing the filter" : "Create your first task to get started"}
                </p>
              </GlassCard>
            </motion.div>
          ) : (
            filteredTasks.map((task) => (
              <motion.div
                key={task.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <TaskItem
                  task={task}
                  onEdit={setEditingTask}
                  onDelete={handleTaskDeleted}
                  onUpdate={handleTaskUpdated}
                />
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </motion.div>

      {/* Create Task Modal - Needs own glass implementation or wrapper */}
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
