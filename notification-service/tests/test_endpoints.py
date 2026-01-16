"""
Unit tests for Notification Service API endpoints using dependency overrides.

This module tests the FastAPI endpoints for notification creation and retrieval,
including authentication, authorization, and error handling scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

# Import the FastAPI app and dependencies
from app.main import app, get_db_session
from app.models import Notification
from app.repository import NotificationRepository

# Import shared utilities with proper path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from jwt_utils import get_current_user


class TestNotificationEndpoints:
    """Test cases for notification service endpoints."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)
        self.mock_db_session = AsyncMock()
        self.mock_repository = MagicMock(spec=NotificationRepository)
        
        # Override dependencies
        async def mock_get_db_session():
            yield self.mock_db_session
        
        def mock_get_current_user():
            return {"user_id": 1, "email": "test@example.com"}
        
        app.dependency_overrides[get_db_session] = mock_get_db_session
        app.dependency_overrides[get_current_user] = mock_get_current_user
    
    def teardown_method(self):
        """Clean up after each test method."""
        app.dependency_overrides.clear()
    
    def test_health_check(self):
        """Test health check endpoint returns correct status."""
        response = self.client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"
    
    def test_create_notification_success(self):
        """Test successful notification creation."""
        # Mock the repository creation and method
        with pytest.MonkeyPatch().context() as m:
            mock_notification = Notification(
                id=1,
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                message="Test notification",
                type="task_assigned",
                is_read=False,
                created_at=datetime(2024, 1, 1, 12, 0, 0)
            )
            
            # Mock the repository class and its create method
            mock_repo_instance = MagicMock()
            mock_repo_instance.create_notification = AsyncMock(return_value=mock_notification)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Test data
            notification_data = {
                "user_id": 1,
                "task_id": "507f1f77bcf86cd799439011",
                "message": "Test notification",
                "type": "task_assigned"
            }
            
            # Make request
            response = self.client.post("/api/v1/notifications", json=notification_data)
            
            # Assertions
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == 1
            assert data["task_id"] == "507f1f77bcf86cd799439011"
            assert data["message"] == "Test notification"
            assert data["type"] == "task_assigned"
            assert data["is_read"] is False
            assert data["created_at"] == "2024-01-01T12:00:00"
    
    def test_create_notification_invalid_type(self):
        """Test notification creation with invalid type."""
        notification_data = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Test notification",
            "type": "invalid_type"
        }
        
        response = self.client.post("/api/v1/notifications", json=notification_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_notification_missing_fields(self):
        """Test notification creation with missing required fields."""
        notification_data = {
            "user_id": 1,
            "message": "Test notification"
            # Missing task_id and type
        }
        
        response = self.client.post("/api/v1/notifications", json=notification_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_notification_invalid_user_id(self):
        """Test notification creation with invalid user_id."""
        notification_data = {
            "user_id": 0,  # Invalid: must be > 0
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Test notification",
            "type": "task_assigned"
        }
        
        response = self.client.post("/api/v1/notifications", json=notification_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_user_notifications_success(self):
        """Test successful retrieval of user notifications."""
        with pytest.MonkeyPatch().context() as m:
            notifications = [
                Notification(
                    id=1,
                    user_id=1,
                    task_id="507f1f77bcf86cd799439011",
                    message="Test notification 1",
                    type="task_assigned",
                    is_read=False,
                    created_at=datetime(2024, 1, 1, 12, 0, 0)
                ),
                Notification(
                    id=2,
                    user_id=1,
                    task_id="507f1f77bcf86cd799439012",
                    message="Test notification 2",
                    type="task_updated",
                    is_read=True,
                    created_at=datetime(2024, 1, 1, 13, 0, 0)
                )
            ]
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_user_notifications = AsyncMock(return_value=notifications)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Make request
            response = self.client.get("/api/v1/notifications")
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 2
            assert len(data["notifications"]) == 2
            
            # Check first notification
            notif1 = data["notifications"][0]
            assert notif1["id"] == 1
            assert notif1["user_id"] == 1
            assert notif1["message"] == "Test notification 1"
            assert notif1["type"] == "task_assigned"
            assert notif1["is_read"] is False
            
            # Verify repository was called with correct parameters
            mock_repo_instance.get_user_notifications.assert_called_once_with(
                user_id=1,
                unread_only=False,
                limit=50
            )
    
    def test_get_user_notifications_unread_only(self):
        """Test retrieval of only unread notifications."""
        with pytest.MonkeyPatch().context() as m:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_user_notifications = AsyncMock(return_value=[])
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Make request with unread_only parameter
            response = self.client.get("/api/v1/notifications?unread_only=true")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called with unread_only=True
            mock_repo_instance.get_user_notifications.assert_called_once_with(
                user_id=1,
                unread_only=True,
                limit=50
            )
    
    def test_get_user_notifications_custom_limit(self):
        """Test retrieval with custom limit parameter."""
        with pytest.MonkeyPatch().context() as m:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_user_notifications = AsyncMock(return_value=[])
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Make request with custom limit
            response = self.client.get("/api/v1/notifications?limit=10")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called with custom limit
            mock_repo_instance.get_user_notifications.assert_called_once_with(
                user_id=1,
                unread_only=False,
                limit=10
            )
    
    def test_get_user_notifications_invalid_limit(self):
        """Test retrieval with invalid limit parameter."""
        # Test limit too high
        response = self.client.get("/api/v1/notifications?limit=101")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test limit too low
        response = self.client.get("/api/v1/notifications?limit=0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_get_user_notifications_no_auth(self):
        """Test retrieval without authentication."""
        # Clear the auth override for this test
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        response = self.client.get("/api/v1/notifications")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_mark_notification_as_read_success(self):
        """Test successfully marking a notification as read."""
        with pytest.MonkeyPatch().context() as m:
            notification = Notification(
                id=1,
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                message="Test notification",
                type="task_assigned",
                is_read=False,
                created_at=datetime(2024, 1, 1, 12, 0, 0)
            )
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_notification_by_id = AsyncMock(return_value=notification)
            mock_repo_instance.mark_notification_as_read = AsyncMock(return_value=True)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Make request
            response = self.client.put("/api/v1/notifications/1/read")
            
            # Assertions
            assert response.status_code == status.HTTP_204_NO_CONTENT
            
            # Verify repository methods were called
            mock_repo_instance.get_notification_by_id.assert_called_once_with(1)
            mock_repo_instance.mark_notification_as_read.assert_called_once_with(1)
    
    def test_mark_notification_as_read_not_found(self):
        """Test marking non-existent notification as read."""
        with pytest.MonkeyPatch().context() as m:
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_notification_by_id = AsyncMock(return_value=None)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            response = self.client.put("/api/v1/notifications/999/read")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Notification not found" in response.json()["detail"]
    
    def test_mark_notification_as_read_access_denied(self):
        """Test marking notification belonging to another user."""
        with pytest.MonkeyPatch().context() as m:
            # Notification belongs to user 2, but current user is 1
            notification = Notification(
                id=1,
                user_id=2,  # Different user
                task_id="507f1f77bcf86cd799439011",
                message="Test notification",
                type="task_assigned",
                is_read=False,
                created_at=datetime(2024, 1, 1, 12, 0, 0)
            )
            
            mock_repo_instance = MagicMock()
            mock_repo_instance.get_notification_by_id = AsyncMock(return_value=notification)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            response = self.client.put("/api/v1/notifications/1/read")
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in response.json()["detail"]
    
    def test_mark_notification_as_read_no_auth(self):
        """Test marking notification as read without authentication."""
        # Clear the auth override for this test
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        response = self.client.put("/api/v1/notifications/1/read")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_mark_all_notifications_as_read_success(self):
        """Test successfully marking all notifications as read."""
        with pytest.MonkeyPatch().context() as m:
            mock_repo_instance = MagicMock()
            mock_repo_instance.mark_user_notifications_as_read = AsyncMock(return_value=3)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            # Make request
            response = self.client.put("/api/v1/notifications/read-all")
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["marked_as_read"] == 3
            
            # Verify repository was called
            mock_repo_instance.mark_user_notifications_as_read.assert_called_once_with(1)
    
    def test_mark_all_notifications_as_read_no_notifications(self):
        """Test marking all notifications as read when none exist."""
        with pytest.MonkeyPatch().context() as m:
            mock_repo_instance = MagicMock()
            mock_repo_instance.mark_user_notifications_as_read = AsyncMock(return_value=0)
            
            m.setattr("app.main.NotificationRepository", lambda session: mock_repo_instance)
            
            response = self.client.put("/api/v1/notifications/read-all")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["marked_as_read"] == 0
    
    def test_mark_all_notifications_as_read_no_auth(self):
        """Test marking all notifications as read without authentication."""
        # Clear the auth override for this test
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        
        response = self.client.put("/api/v1/notifications/read-all")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN