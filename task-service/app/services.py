"""
Task Service business logic layer.
Handles task operations and business rules.
"""

import logging
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import TaskCreate, TaskUpdate, TaskInDB, TaskResponse, TaskStatus, task_helper
from .repository import TaskRepository
from .notification_client import get_notification_client

logger = logging.getLogger(__name__)


class TaskService:
    """Service class for task business logic."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.repository = TaskRepository(database)
    
    async def create_task(self, task_data: TaskCreate, creator_id: int) -> TaskResponse:
        """Create a new task."""
        try:
            # Create task in database
            created_task = await self.repository.create_task(task_data, creator_id)
            
            # Convert to response format
            return TaskResponse(
                id=str(created_task.id),
                title=created_task.title,
                description=created_task.description,
                due_date=created_task.due_date,
                status=created_task.status,
                creator_id=created_task.creator_id,
                assignee_id=created_task.assignee_id,
                created_at=created_task.created_at,
                updated_at=created_task.updated_at
            )
            
        except Exception as e:
            raise Exception(f"Failed to create task: {str(e)}")
    
    async def get_task_by_id(self, task_id: str, user_id: int) -> Optional[TaskResponse]:
        """Get a task by ID if user has access."""
        try:
            task = await self.repository.get_task_by_id(task_id)
            
            if not task:
                return None
            
            # Check if user has access to this task
            if task.creator_id != user_id and task.assignee_id != user_id:
                raise PermissionError("User does not have access to this task")
            
            return TaskResponse(
                id=str(task.id),
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                status=task.status,
                creator_id=task.creator_id,
                assignee_id=task.assignee_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to retrieve task: {str(e)}")
    
    async def get_user_tasks(self, user_id: int, skip: int = 0, limit: int = 100) -> List[TaskResponse]:
        """Get all tasks for a user (created or assigned)."""
        try:
            tasks = await self.repository.get_tasks_by_user(user_id, skip, limit)
            
            return [
                TaskResponse(
                    id=str(task.id),
                    title=task.title,
                    description=task.description,
                    due_date=task.due_date,
                    status=task.status,
                    creator_id=task.creator_id,
                    assignee_id=task.assignee_id,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                for task in tasks
            ]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve user tasks: {str(e)}")
    
    async def get_tasks_by_status(self, user_id: int, status: str, skip: int = 0, limit: int = 100) -> List[TaskResponse]:
        """Get tasks by status for a user."""
        try:
            tasks = await self.repository.get_tasks_by_status(status, user_id, skip, limit)
            
            return [
                TaskResponse(
                    id=str(task.id),
                    title=task.title,
                    description=task.description,
                    due_date=task.due_date,
                    status=task.status,
                    creator_id=task.creator_id,
                    assignee_id=task.assignee_id,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                for task in tasks
            ]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve tasks by status: {str(e)}")
    
    async def update_task(self, task_id: str, task_update: TaskUpdate, user_id: int) -> Optional[TaskResponse]:
        """Update a task."""
        try:
            updated_task = await self.repository.update_task(task_id, task_update, user_id)
            
            if not updated_task:
                return None
            
            return TaskResponse(
                id=str(updated_task.id),
                title=updated_task.title,
                description=updated_task.description,
                due_date=updated_task.due_date,
                status=updated_task.status,
                creator_id=updated_task.creator_id,
                assignee_id=updated_task.assignee_id,
                created_at=updated_task.created_at,
                updated_at=updated_task.updated_at
            )
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to update task: {str(e)}")
    
    async def delete_task(self, task_id: str, user_id: int) -> bool:
        """Delete a task (only creator can delete)."""
        try:
            return await self.repository.delete_task(task_id, user_id)
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete task: {str(e)}")
    
    async def count_user_tasks(self, user_id: int) -> int:
        """Count total tasks for a user."""
        try:
            return await self.repository.count_user_tasks(user_id)
            
        except Exception as e:
            raise Exception(f"Failed to count user tasks: {str(e)}")
    
    async def assign_task(self, task_id: str, assignee_id: int, user_id: int) -> Optional[TaskResponse]:
        """Assign a task to a user."""
        try:
            # Get the task first
            task = await self.repository.get_task_by_id(task_id)
            if not task:
                return None
            
            # Check if user can assign this task
            if task.creator_id != user_id:
                raise PermissionError("Only task creator can assign tasks")
            
            # TODO: Validate that assignee_id exists in User Service
            # For now, we'll accept any positive integer as valid user ID
            if assignee_id <= 0:
                raise ValueError("Invalid assignee ID")
            
            # Store previous assignee for comparison
            previous_assignee = task.assignee_id
            
            # Update task with new assignee
            update_data = TaskUpdate(assignee_id=assignee_id)
            updated_task = await self.update_task(task_id, update_data, user_id)
            
            # Send notification if task was successfully assigned to a new user
            if updated_task and assignee_id != previous_assignee:
                try:
                    notification_client = get_notification_client()
                    await notification_client.create_task_assigned_notification(
                        assignee_id=assignee_id,
                        task_id=task_id,
                        task_title=updated_task.title,
                        assigner_name=f"User {user_id}"  # TODO: Get actual user name
                    )
                    logger.info(f"Notification sent for task assignment: {task_id} -> user {assignee_id}")
                except Exception as e:
                    logger.error(f"Failed to send assignment notification: {str(e)}")
                    # Don't fail the assignment if notification fails
            
            return updated_task
            
        except (PermissionError, ValueError):
            raise
        except Exception as e:
            raise Exception(f"Failed to assign task: {str(e)}")
    
    async def unassign_task(self, task_id: str, user_id: int) -> Optional[TaskResponse]:
        """Remove assignment from a task."""
        try:
            # Get the task first
            task = await self.repository.get_task_by_id(task_id)
            if not task:
                return None
            
            # Check if user can unassign this task
            if task.creator_id != user_id:
                raise PermissionError("Only task creator can unassign tasks")
            
            # Update task to remove assignee
            update_data = TaskUpdate(assignee_id=None)
            return await self.update_task(task_id, update_data, user_id)
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to unassign task: {str(e)}")
    
    async def change_task_status(self, task_id: str, new_status: TaskStatus, user_id: int) -> Optional[TaskResponse]:
        """Change task status with proper validation."""
        try:
            # Get the task first
            task = await self.repository.get_task_by_id(task_id)
            if not task:
                return None
            
            # Check if user can change status
            if task.creator_id != user_id and task.assignee_id != user_id:
                raise PermissionError("Only task creator or assignee can change status")
            
            # Additional validation for status changes
            if task.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
                # Only creator can reopen completed tasks
                if task.creator_id != user_id:
                    raise PermissionError("Only task creator can reopen completed tasks")
            
            # Store previous status for comparison
            previous_status = task.status
            
            # Update task status
            update_data = TaskUpdate(status=new_status)
            updated_task = await self.update_task(task_id, update_data, user_id)
            
            # Send notifications if status was successfully changed
            if updated_task and new_status != previous_status:
                try:
                    notification_client = get_notification_client()
                    
                    # Notify both creator and assignee (if different from updater)
                    users_to_notify = []
                    
                    # Add creator if they're not the one updating
                    if task.creator_id != user_id:
                        users_to_notify.append(task.creator_id)
                    
                    # Add assignee if they exist and are not the one updating
                    if task.assignee_id and task.assignee_id != user_id:
                        users_to_notify.append(task.assignee_id)
                    
                    # Send notifications to relevant users
                    for notify_user_id in users_to_notify:
                        await notification_client.create_task_status_notification(
                            user_id=notify_user_id,
                            task_id=task_id,
                            task_title=updated_task.title,
                            new_status=new_status.value,
                            updater_name=f"User {user_id}"  # TODO: Get actual user name
                        )
                    
                    if users_to_notify:
                        logger.info(f"Status update notifications sent for task {task_id} to users: {users_to_notify}")
                    
                except Exception as e:
                    logger.error(f"Failed to send status update notifications: {str(e)}")
                    # Don't fail the status update if notification fails
            
            return updated_task
            
        except PermissionError:
            raise
        except Exception as e:
            raise Exception(f"Failed to change task status: {str(e)}")
    
    async def get_assigned_tasks(self, assignee_id: int, skip: int = 0, limit: int = 100) -> List[TaskResponse]:
        """Get tasks assigned to a specific user."""
        try:
            tasks = await self.repository.get_tasks_by_assignee(assignee_id, skip, limit)
            
            return [
                TaskResponse(
                    id=str(task.id),
                    title=task.title,
                    description=task.description,
                    due_date=task.due_date,
                    status=task.status,
                    creator_id=task.creator_id,
                    assignee_id=task.assignee_id,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                for task in tasks
            ]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve assigned tasks: {str(e)}")
    
    async def get_created_tasks(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[TaskResponse]:
        """Get tasks created by a specific user."""
        try:
            tasks = await self.repository.get_tasks_by_creator(creator_id, skip, limit)
            
            return [
                TaskResponse(
                    id=str(task.id),
                    title=task.title,
                    description=task.description,
                    due_date=task.due_date,
                    status=task.status,
                    creator_id=task.creator_id,
                    assignee_id=task.assignee_id,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                for task in tasks
            ]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve created tasks: {str(e)}")


async def get_task_service(database: AsyncIOMotorDatabase) -> TaskService:
    """Dependency function to get task service instance."""
    return TaskService(database)