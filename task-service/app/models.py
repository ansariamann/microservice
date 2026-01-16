"""
Task Service data models and schemas.
Defines the Task document structure and validation rules.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core import core_schema


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class TaskBase(BaseModel):
    """Base task model with common fields."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(..., max_length=2000, description="Task description")
    due_date: datetime = Field(..., description="Task due date")
    status: TaskStatus = Field(default=TaskStatus.TO_DO, description="Task status")
    assignee_id: Optional[int] = Field(None, description="ID of assigned user")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        return v.strip() if v else ""
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v < datetime.now():
            raise ValueError('Due date cannot be in the past')
        return v


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[int] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Title cannot be empty')
            return v.strip()
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            return v.strip()
        return v
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v is not None and v < datetime.now():
            raise ValueError('Due date cannot be in the past')
        return v


class Task(TaskBase):
    """Complete task model with database fields."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    creator_id: int = Field(..., description="ID of task creator")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the task management system",
                "due_date": "2024-12-31T23:59:59",
                "status": "to_do",
                "creator_id": 1,
                "assignee_id": 2
            }
        }
    )


class TaskInDB(Task):
    """Task model as stored in database."""
    pass


class TaskResponse(BaseModel):
    """Task model for API responses."""
    
    id: str
    title: str
    description: str
    due_date: datetime
    status: TaskStatus
    creator_id: int
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Complete project documentation",
                "description": "Write comprehensive documentation for the task management system",
                "due_date": "2024-12-31T23:59:59",
                "status": "to_do",
                "creator_id": 1,
                "assignee_id": 2,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


def task_helper(task) -> dict:
    """Helper function to convert MongoDB document to dictionary."""
    return {
        "id": str(task["_id"]),
        "title": task["title"],
        "description": task["description"],
        "due_date": task["due_date"],
        "status": task["status"],
        "creator_id": task["creator_id"],
        "assignee_id": task.get("assignee_id"),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }