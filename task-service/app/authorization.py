"""
Authorization utilities for Task Service.
Handles task access control and permission checks.
"""

from typing import Optional
from .models import TaskInDB, TaskStatus


class TaskAuthorization:
    """Task authorization and access control utilities."""
    
    @staticmethod
    def can_view_task(task: TaskInDB, user_id: int) -> bool:
        """Check if user can view a task."""
        return (
            task.creator_id == user_id or 
            task.assignee_id == user_id
        )
    
    @staticmethod
    def can_edit_task(task: TaskInDB, user_id: int) -> bool:
        """Check if user can edit a task."""
        return (
            task.creator_id == user_id or 
            task.assignee_id == user_id
        )
    
    @staticmethod
    def can_delete_task(task: TaskInDB, user_id: int) -> bool:
        """Check if user can delete a task."""
        # Only creator can delete tasks
        return task.creator_id == user_id
    
    @staticmethod
    def can_assign_task(task: TaskInDB, user_id: int) -> bool:
        """Check if user can assign/reassign a task."""
        # Only creator can assign tasks
        return task.creator_id == user_id
    
    @staticmethod
    def can_change_status(task: TaskInDB, user_id: int, new_status: TaskStatus) -> bool:
        """Check if user can change task status."""
        # Both creator and assignee can change status
        if not (task.creator_id == user_id or task.assignee_id == user_id):
            return False
        
        # Additional business rules for status changes
        if task.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            # Only creator can reopen completed tasks
            return task.creator_id == user_id
        
        return True
    
    @staticmethod
    def filter_user_accessible_tasks(tasks: list[TaskInDB], user_id: int) -> list[TaskInDB]:
        """Filter tasks to only include those accessible by the user."""
        return [
            task for task in tasks 
            if TaskAuthorization.can_view_task(task, user_id)
        ]
    
    @staticmethod
    def validate_task_access(task: Optional[TaskInDB], user_id: int, action: str = "view") -> None:
        """Validate task access and raise PermissionError if denied."""
        if not task:
            raise ValueError("Task not found")
        
        permission_methods = {
            "view": TaskAuthorization.can_view_task,
            "edit": TaskAuthorization.can_edit_task,
            "delete": TaskAuthorization.can_delete_task,
            "assign": TaskAuthorization.can_assign_task
        }
        
        permission_method = permission_methods.get(action)
        if not permission_method:
            raise ValueError(f"Unknown action: {action}")
        
        if not permission_method(task, user_id):
            raise PermissionError(f"User {user_id} does not have permission to {action} task {task.id}")
    
    @staticmethod
    def validate_status_change(task: TaskInDB, user_id: int, new_status: TaskStatus) -> None:
        """Validate status change permission."""
        if not TaskAuthorization.can_change_status(task, user_id, new_status):
            raise PermissionError(f"User {user_id} cannot change task status from {task.status} to {new_status}")


# Convenience functions for common authorization checks
def require_task_access(task: Optional[TaskInDB], user_id: int, action: str = "view") -> TaskInDB:
    """Require task access or raise PermissionError."""
    TaskAuthorization.validate_task_access(task, user_id, action)
    return task


def require_task_ownership(task: Optional[TaskInDB], user_id: int) -> TaskInDB:
    """Require task ownership (creator) or raise PermissionError."""
    if not task:
        raise ValueError("Task not found")
    
    if task.creator_id != user_id:
        raise PermissionError(f"User {user_id} is not the owner of task {task.id}")
    
    return task


def check_assignee_permission(task: TaskInDB, user_id: int, assignee_id: Optional[int]) -> None:
    """Check if user can assign task to the specified assignee."""
    if assignee_id is not None and not TaskAuthorization.can_assign_task(task, user_id):
        raise PermissionError(f"User {user_id} cannot assign task {task.id}")


def get_user_task_filter(user_id: int) -> dict:
    """Get MongoDB filter for user-accessible tasks."""
    return {
        "$or": [
            {"creator_id": user_id},
            {"assignee_id": user_id}
        ]
    }