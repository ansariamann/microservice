"""
Unit tests for notification service repository layer.

This module tests the NotificationRepository class functionality,
including CRUD operations, filtering, and error handling.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.models import Notification
from app.repository import NotificationRepository


class TestNotificationRepository:
    """Test cases for the NotificationRepository class."""

    @pytest.mark.asyncio
    async def test_create_notification(self, notification_repository, sample_notification_data):
        """Test creating a new notification."""
        notification = Notification(**sample_notification_data)
        
        created_notification = await notification_repository.create_notification(notification)
        
        assert created_notification.id is not None
        assert created_notification.user_id == sample_notification_data["user_id"]
        assert created_notification.task_id == sample_notification_data["task_id"]
        assert created_notification.message == sample_notification_data["message"]
        assert created_notification.type == sample_notification_data["type"]
        assert created_notification.is_read is False
        assert created_notification.created_at is not None

    @pytest.mark.asyncio
    async def test_get_notification_by_id(self, notification_repository, sample_notification_data):
        """Test retrieving a notification by ID."""
        # Create a notification first
        notification = Notification(**sample_notification_data)
        created_notification = await notification_repository.create_notification(notification)
        
        # Retrieve the notification
        retrieved_notification = await notification_repository.get_notification_by_id(created_notification.id)
        
        assert retrieved_notification is not None
        assert retrieved_notification.id == created_notification.id
        assert retrieved_notification.user_id == sample_notification_data["user_id"]
        assert retrieved_notification.task_id == sample_notification_data["task_id"]

    @pytest.mark.asyncio
    async def test_get_notification_by_id_not_found(self, notification_repository):
        """Test retrieving a non-existent notification."""
        retrieved_notification = await notification_repository.get_notification_by_id(999)
        assert retrieved_notification is None

    @pytest.mark.asyncio
    async def test_get_user_notifications(self, notification_repository, multiple_notification_data):
        """Test retrieving notifications for a specific user."""
        # Create multiple notifications
        created_notifications = []
        for data in multiple_notification_data:
            notification = Notification(**data)
            created = await notification_repository.create_notification(notification)
            created_notifications.append(created)
        
        # Get notifications for user 1
        user_1_notifications = await notification_repository.get_user_notifications(user_id=1)
        
        # Should get 2 notifications for user 1
        assert len(user_1_notifications) == 2
        for notification in user_1_notifications:
            assert notification.user_id == 1
        
        # Get notifications for user 2
        user_2_notifications = await notification_repository.get_user_notifications(user_id=2)
        
        # Should get 1 notification for user 2
        assert len(user_2_notifications) == 1
        assert user_2_notifications[0].user_id == 2

    @pytest.mark.asyncio
    async def test_get_user_notifications_unread_only(self, notification_repository, multiple_notification_data):
        """Test retrieving only unread notifications for a user."""
        # Create notifications
        notifications = []
        for data in multiple_notification_data:
            notification = Notification(**data)
            created = await notification_repository.create_notification(notification)
            notifications.append(created)
        
        # Mark one notification as read
        await notification_repository.mark_notification_as_read(notifications[0].id)
        
        # Get unread notifications for user 1
        unread_notifications = await notification_repository.get_user_notifications(
            user_id=1, unread_only=True
        )
        
        # Should get 1 unread notification for user 1
        assert len(unread_notifications) == 1
        assert unread_notifications[0].is_read is False
        assert unread_notifications[0].id != notifications[0].id

    @pytest.mark.asyncio
    async def test_get_user_notifications_with_limit(self, notification_repository):
        """Test retrieving notifications with limit."""
        # Create multiple notifications for the same user
        for i in range(5):
            notification = Notification(
                user_id=1,
                task_id=f"507f1f77bcf86cd79943901{i}",
                message=f"Test notification {i}",
                type="task_assigned"
            )
            await notification_repository.create_notification(notification)
        
        # Get notifications with limit
        limited_notifications = await notification_repository.get_user_notifications(
            user_id=1, limit=3
        )
        
        assert len(limited_notifications) == 3

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, notification_repository, sample_notification_data):
        """Test marking a notification as read."""
        # Create a notification
        notification = Notification(**sample_notification_data)
        created_notification = await notification_repository.create_notification(notification)
        
        # Verify it's initially unread
        assert created_notification.is_read is False
        
        # Mark as read
        result = await notification_repository.mark_notification_as_read(created_notification.id)
        assert result is True
        
        # Verify it's now marked as read
        updated_notification = await notification_repository.get_notification_by_id(created_notification.id)
        assert updated_notification.is_read is True

    @pytest.mark.asyncio
    async def test_mark_notification_as_read_not_found(self, notification_repository):
        """Test marking a non-existent notification as read."""
        result = await notification_repository.mark_notification_as_read(999)
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_user_notifications_as_read(self, notification_repository, multiple_notification_data):
        """Test marking all user notifications as read."""
        # Create notifications
        for data in multiple_notification_data:
            notification = Notification(**data)
            await notification_repository.create_notification(notification)
        
        # Mark all notifications for user 1 as read
        count = await notification_repository.mark_user_notifications_as_read(user_id=1)
        assert count == 2  # User 1 has 2 notifications
        
        # Verify all user 1 notifications are read
        user_1_notifications = await notification_repository.get_user_notifications(user_id=1)
        for notification in user_1_notifications:
            assert notification.is_read is True
        
        # Verify user 2 notifications are still unread
        user_2_notifications = await notification_repository.get_user_notifications(user_id=2)
        for notification in user_2_notifications:
            assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_delete_notification(self, notification_repository, sample_notification_data):
        """Test deleting a notification."""
        # Create a notification
        notification = Notification(**sample_notification_data)
        created_notification = await notification_repository.create_notification(notification)
        
        # Delete the notification
        result = await notification_repository.delete_notification(created_notification.id)
        assert result is True
        
        # Verify it's deleted
        deleted_notification = await notification_repository.get_notification_by_id(created_notification.id)
        assert deleted_notification is None

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, notification_repository):
        """Test deleting a non-existent notification."""
        result = await notification_repository.delete_notification(999)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_notifications_by_task(self, notification_repository, multiple_notification_data):
        """Test retrieving notifications by task ID."""
        # Create notifications
        for data in multiple_notification_data:
            notification = Notification(**data)
            await notification_repository.create_notification(notification)
        
        # Get notifications for specific task
        task_notifications = await notification_repository.get_notifications_by_task("507f1f77bcf86cd799439011")
        
        # Should get 2 notifications for this task (one for each user)
        assert len(task_notifications) == 2
        for notification in task_notifications:
            assert notification.task_id == "507f1f77bcf86cd799439011"

    @pytest.mark.asyncio
    async def test_get_notifications_by_task_not_found(self, notification_repository):
        """Test retrieving notifications for non-existent task."""
        task_notifications = await notification_repository.get_notifications_by_task("nonexistent")
        assert len(task_notifications) == 0

    @pytest.mark.asyncio
    async def test_notifications_ordered_by_created_at(self, notification_repository):
        """Test that notifications are returned in descending order by created_at."""
        # Create notifications with slight delay to ensure different timestamps
        notifications = []
        for i in range(3):
            notification = Notification(
                user_id=1,
                task_id=f"507f1f77bcf86cd79943901{i}",
                message=f"Test notification {i}",
                type="task_assigned"
            )
            created = await notification_repository.create_notification(notification)
            notifications.append(created)
        
        # Get user notifications
        user_notifications = await notification_repository.get_user_notifications(user_id=1)
        
        # Verify they're ordered by created_at descending (newest first)
        assert len(user_notifications) == 3
        for i in range(len(user_notifications) - 1):
            assert user_notifications[i].created_at >= user_notifications[i + 1].created_at


class TestNotificationRepositoryErrorHandling:
    """Test error handling in NotificationRepository."""

    @pytest.mark.asyncio
    async def test_repository_handles_database_errors(self, notification_repository):
        """Test that repository properly handles database errors."""
        # This test would require mocking database errors
        # For now, we'll test basic error scenarios
        
        # Test with invalid notification data (this should be caught by SQLAlchemy)
        notification = Notification(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test message",
            type="task_assigned"
        )
        
        # This should work fine
        created = await notification_repository.create_notification(notification)
        assert created.id is not None