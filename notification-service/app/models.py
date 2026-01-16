"""
Notification Service Database Models

This module defines the SQLAlchemy models for the notification service,
including the Notification model with proper schema definition.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Optional

Base = declarative_base()


class Notification(Base):
    """
    Notification model for storing task-related notifications.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        user_id: ID of the user who should receive the notification
        task_id: ID of the task this notification relates to (stored as string for MongoDB compatibility)
        message: The notification message content
        type: Type of notification ('task_assigned', 'task_updated')
        is_read: Boolean flag indicating if the notification has been read
        created_at: Timestamp when the notification was created
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_id = Column(String(50), nullable=False)  # MongoDB ObjectId as string
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # 'task_assigned', 'task_updated'
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, **kwargs):
        """Initialize notification with default values."""
        if 'is_read' not in kwargs:
            kwargs['is_read'] = False
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', is_read={self.is_read})>"

    def to_dict(self) -> dict:
        """Convert notification to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def create_task_assigned_notification(
        cls, 
        user_id: int, 
        task_id: str, 
        task_title: str, 
        assigner_name: str
    ) -> "Notification":
        """Create a task assignment notification."""
        message = f"You have been assigned to task '{task_title}' by {assigner_name}"
        return cls(
            user_id=user_id,
            task_id=task_id,
            message=message,
            type="task_assigned"
        )

    @classmethod
    def create_task_updated_notification(
        cls, 
        user_id: int, 
        task_id: str, 
        task_title: str, 
        status: str
    ) -> "Notification":
        """Create a task status update notification."""
        message = f"Task '{task_title}' status has been updated to '{status}'"
        return cls(
            user_id=user_id,
            task_id=task_id,
            message=message,
            type="task_updated"
        )