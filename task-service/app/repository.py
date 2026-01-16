"""
Task repository for MongoDB operations.
Handles all database interactions for task management.
"""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import Task, TaskCreate, TaskUpdate, TaskInDB, task_helper


class TaskRepository:
    """Repository class for task database operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.tasks
    
    async def create_task(self, task_data: TaskCreate, creator_id: int) -> TaskInDB:
        """Create a new task in the database."""
        try:
            task_dict = task_data.dict()
            task_dict["creator_id"] = creator_id
            task_dict["created_at"] = datetime.now()
            task_dict["updated_at"] = datetime.now()
            
            result = await self.collection.insert_one(task_dict)
            
            if result.inserted_id:
                created_task = await self.collection.find_one({"_id": result.inserted_id})
                return TaskInDB(**created_task)
            
            raise PyMongoError("Failed to create task")
            
        except PyMongoError as e:
            raise Exception(f"Database error creating task: {str(e)}")
    
    async def get_task_by_id(self, task_id: str) -> Optional[TaskInDB]:
        """Retrieve a task by its ID."""
        try:
            if not ObjectId.is_valid(task_id):
                return None
            
            task = await self.collection.find_one({"_id": ObjectId(task_id)})
            
            if task:
                return TaskInDB(**task)
            return None
            
        except PyMongoError as e:
            raise Exception(f"Database error retrieving task: {str(e)}")
    
    async def get_tasks_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[TaskInDB]:
        """Retrieve tasks where user is creator or assignee."""
        try:
            cursor = self.collection.find({
                "$or": [
                    {"creator_id": user_id},
                    {"assignee_id": user_id}
                ]
            }).skip(skip).limit(limit).sort("created_at", -1)
            
            tasks = []
            async for task in cursor:
                tasks.append(TaskInDB(**task))
            
            return tasks
            
        except PyMongoError as e:
            raise Exception(f"Database error retrieving user tasks: {str(e)}")
    
    async def get_tasks_by_creator(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[TaskInDB]:
        """Retrieve tasks created by a specific user."""
        try:
            cursor = self.collection.find({"creator_id": creator_id}).skip(skip).limit(limit).sort("created_at", -1)
            
            tasks = []
            async for task in cursor:
                tasks.append(TaskInDB(**task))
            
            return tasks
            
        except PyMongoError as e:
            raise Exception(f"Database error retrieving creator tasks: {str(e)}")
    
    async def get_tasks_by_assignee(self, assignee_id: int, skip: int = 0, limit: int = 100) -> List[TaskInDB]:
        """Retrieve tasks assigned to a specific user."""
        try:
            cursor = self.collection.find({"assignee_id": assignee_id}).skip(skip).limit(limit).sort("created_at", -1)
            
            tasks = []
            async for task in cursor:
                tasks.append(TaskInDB(**task))
            
            return tasks
            
        except PyMongoError as e:
            raise Exception(f"Database error retrieving assigned tasks: {str(e)}")
    
    async def update_task(self, task_id: str, task_update: TaskUpdate, user_id: int) -> Optional[TaskInDB]:
        """Update an existing task."""
        try:
            if not ObjectId.is_valid(task_id):
                return None
            
            # First check if task exists and user has permission
            existing_task = await self.get_task_by_id(task_id)
            if not existing_task:
                return None
            
            # Check if user is creator or assignee
            if existing_task.creator_id != user_id and existing_task.assignee_id != user_id:
                raise PermissionError("User does not have permission to update this task")
            
            # Prepare update data
            update_data = {}
            for field, value in task_update.dict(exclude_unset=True).items():
                if value is not None:
                    update_data[field] = value
            
            if update_data:
                update_data["updated_at"] = datetime.now()
                
                result = await self.collection.update_one(
                    {"_id": ObjectId(task_id)},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updated_task = await self.collection.find_one({"_id": ObjectId(task_id)})
                    return TaskInDB(**updated_task)
            
            return existing_task
            
        except PermissionError:
            raise
        except PyMongoError as e:
            raise Exception(f"Database error updating task: {str(e)}")
    
    async def delete_task(self, task_id: str, user_id: int) -> bool:
        """Delete a task (only creator can delete)."""
        try:
            if not ObjectId.is_valid(task_id):
                return False
            
            # Check if task exists and user is creator
            existing_task = await self.get_task_by_id(task_id)
            if not existing_task:
                return False
            
            if existing_task.creator_id != user_id:
                raise PermissionError("Only task creator can delete the task")
            
            result = await self.collection.delete_one({"_id": ObjectId(task_id)})
            return result.deleted_count > 0
            
        except PermissionError:
            raise
        except PyMongoError as e:
            raise Exception(f"Database error deleting task: {str(e)}")
    
    async def get_tasks_by_status(self, status: str, user_id: int, skip: int = 0, limit: int = 100) -> List[TaskInDB]:
        """Retrieve tasks by status for a specific user."""
        try:
            cursor = self.collection.find({
                "$and": [
                    {"status": status},
                    {"$or": [
                        {"creator_id": user_id},
                        {"assignee_id": user_id}
                    ]}
                ]
            }).skip(skip).limit(limit).sort("created_at", -1)
            
            tasks = []
            async for task in cursor:
                tasks.append(TaskInDB(**task))
            
            return tasks
            
        except PyMongoError as e:
            raise Exception(f"Database error retrieving tasks by status: {str(e)}")
    
    async def count_user_tasks(self, user_id: int) -> int:
        """Count total tasks for a user."""
        try:
            count = await self.collection.count_documents({
                "$or": [
                    {"creator_id": user_id},
                    {"assignee_id": user_id}
                ]
            })
            return count
            
        except PyMongoError as e:
            raise Exception(f"Database error counting tasks: {str(e)}")