"""
Unit tests for notification service database models.

This module tests the Notification model functionality,
including model creation, validation, and helper methods.
"""

import pytest
from datetime import datetime
from app.models import Notification


class TestNotificationModel:
    """Test cases for the Notification model."""

    def test_notification_creation(self):
        """Test basic notification creation."""
        notification = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification message",
            type="task_assigned"
        )
        
        assert notification.user_id == 1
        assert notification.task_id == "507f1f77bcf86cd799439011"
        assert notification.message == "Test notification message"
        assert notification.type == "task_assigned"
        assert notification.is_read is False  # Default value
        assert notification.id is None  # Not set until saved to DB

    def test_notification_repr(self):
        """Test notification string representation."""
        notification = Notification(
            id=1,
            user_id=2,
            task_id="507f1f77bcf86cd799439011",
            message="Test message",
            type="task_updated",
            is_read=True
        )
        
        expected = "<Notification(id=1, user_id=2, type='task_updated', is_read=True)>"
        assert repr(notification) == expected

    def test_notification_to_dict(self):
        """Test notification dictionary conversion."""
        created_at = datetime.now()
        notification = Notification(
            id=1,
            user_id=2,
            task_id="507f1f77bcf86cd799439011",
            message="Test message",
            type="task_assigned",
            is_read=False,
            created_at=created_at
        )
        
        result = notification.to_dict()
        
        expected = {
            "id": 1,
            "user_id": 2,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Test message",
            "type": "task_assigned",
            "is_read": False,
            "created_at": created_at.isoformat()
        }
        
        assert result == expected

    def test_notification_to_dict_no_created_at(self):
        """Test notification dictionary conversion when created_at is None."""
        notification = Notification(
            id=1,
            user_id=2,
            task_id="507f1f77bcf86cd799439011",
            message="Test message",
            type="task_assigned",
            is_read=False
        )
        
        result = notification.to_dict()
        assert result["created_at"] is None

    def test_create_task_assigned_notification(self):
        """Test factory method for task assignment notifications."""
        notification = Notification.create_task_assigned_notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            task_title="Complete project setup",
            assigner_name="John Doe"
        )
        
        assert notification.user_id == 1
        assert notification.task_id == "507f1f77bcf86cd799439011"
        assert notification.type == "task_assigned"
        assert notification.is_read is False
        assert "Complete project setup" in notification.message
        assert "John Doe" in notification.message
        expected_message = "You have been assigned to task 'Complete project setup' by John Doe"
        assert notification.message == expected_message

    def test_create_task_updated_notification(self):
        """Test factory method for task update notifications."""
        notification = Notification.create_task_updated_notification(
            user_id=2,
            task_id="507f1f77bcf86cd799439012",
            task_title="Review code changes",
            status="in_progress"
        )
        
        assert notification.user_id == 2
        assert notification.task_id == "507f1f77bcf86cd799439012"
        assert notification.type == "task_updated"
        assert notification.is_read is False
        assert "Review code changes" in notification.message
        assert "in_progress" in notification.message
        expected_message = "Task 'Review code changes' status has been updated to 'in_progress'"
        assert notification.message == expected_message

    def test_notification_default_values(self):
        """Test that notification has correct default values."""
        notification = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test message",
            type="task_assigned"
        )
        
        # Test default values
        assert notification.is_read is False
        assert notification.id is None
        assert notification.created_at is None  # Will be set by database

    def test_notification_type_validation(self):
        """Test notification with different valid types."""
        # Test task_assigned type
        notification1 = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Assignment message",
            type="task_assigned"
        )
        assert notification1.type == "task_assigned"
        
        # Test task_updated type
        notification2 = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Update message",
            type="task_updated"
        )
        assert notification2.type == "task_updated"

    def test_notification_with_read_status(self):
        """Test notification with different read statuses."""
        # Test unread notification
        unread_notification = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Unread message",
            type="task_assigned",
            is_read=False
        )
        assert unread_notification.is_read is False
        
        # Test read notification
        read_notification = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Read message",
            type="task_assigned",
            is_read=True
        )
        assert read_notification.is_read is True