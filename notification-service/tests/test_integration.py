"""
Integration tests for Notification Service workflows.

This module tests complete notification workflows including database operations,
API endpoints, authentication flows, and service-to-service communication patterns.
"""

import pytest
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any
from fastapi.testclient import TestClient
from fastapi import status

# Import the FastAPI app and dependencies
from app.main import app, get_db_session
from app.models import Notification
from app.database import get_test_db_manager, DatabaseManager
from app.repository import NotificationRepository

# Import shared utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from jwt_utils import create_jwt_token


class TestNotificationIntegration:
    """Integration tests for notification service workflows."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.client = TestClient(app)
    
    def create_test_jwt_token(self, user_id: int = 1, email: str = "test@example.com") -> str:
        """Create a test JWT token for authentication."""
        return create_jwt_token(user_id, email)
    
    def get_auth_headers(self, user_id: int = 1, email: str = "test@example.com") -> Dict[str, str]:
        """Get authorization headers with JWT token."""
        token = self.create_test_jwt_token(user_id, email)
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_complete_notification_workflow(self):
        """Test complete notification creation and retrieval workflow."""
        # Step 1: Create a notification (internal service call)
        notification_data = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "You have been assigned to task 'Integration Test Task' by John Doe",
            "type": "task_assigned"
        }
        
        # Create notification without authentication (internal endpoint)
        create_response = self.client.post("/api/v1/notifications", json=notification_data)
        
        assert create_response.status_code == status.HTTP_201_CREATED
        created_notification = create_response.json()
        assert created_notification["user_id"] == 1
        assert created_notification["task_id"] == "507f1f77bcf86cd799439011"
        assert created_notification["type"] == "task_assigned"
        assert created_notification["is_read"] is False
        notification_id = created_notification["id"]
        
        # Step 2: Retrieve notifications as authenticated user
        auth_headers = self.get_auth_headers(user_id=1)
        get_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        
        assert get_response.status_code == status.HTTP_200_OK
        notifications_data = get_response.json()
        assert notifications_data["total"] == 1
        assert len(notifications_data["notifications"]) == 1
        
        retrieved_notification = notifications_data["notifications"][0]
        assert retrieved_notification["id"] == notification_id
        assert retrieved_notification["user_id"] == 1
        assert retrieved_notification["is_read"] is False
        
        # Step 3: Mark notification as read
        mark_read_response = self.client.put(
            f"/api/v1/notifications/{notification_id}/read",
            headers=auth_headers
        )
        
        assert mark_read_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Step 4: Verify notification is marked as read
        get_after_read_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        
        assert get_after_read_response.status_code == status.HTTP_200_OK
        updated_notifications = get_after_read_response.json()
        assert updated_notifications["notifications"][0]["is_read"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_users_notification_isolation(self):
        """Test that users can only see their own notifications."""
        # Create notifications for different users
        user1_notification = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Notification for user 1",
            "type": "task_assigned"
        }
        
        user2_notification = {
            "user_id": 2,
            "task_id": "507f1f77bcf86cd799439012",
            "message": "Notification for user 2",
            "type": "task_updated"
        }
        
        # Create both notifications
        self.client.post("/api/v1/notifications", json=user1_notification)
        self.client.post("/api/v1/notifications", json=user2_notification)
        
        # User 1 should only see their notification
        user1_headers = self.get_auth_headers(user_id=1, email="user1@example.com")
        user1_response = self.client.get("/api/v1/notifications", headers=user1_headers)
        
        assert user1_response.status_code == status.HTTP_200_OK
        user1_data = user1_response.json()
        assert user1_data["total"] == 1
        assert user1_data["notifications"][0]["user_id"] == 1
        assert user1_data["notifications"][0]["message"] == "Notification for user 1"
        
        # User 2 should only see their notification
        user2_headers = self.get_auth_headers(user_id=2, email="user2@example.com")
        user2_response = self.client.get("/api/v1/notifications", headers=user2_headers)
        
        assert user2_response.status_code == status.HTTP_200_OK
        user2_data = user2_response.json()
        assert user2_data["total"] == 1
        assert user2_data["notifications"][0]["user_id"] == 2
        assert user2_data["notifications"][0]["message"] == "Notification for user 2"
    
    @pytest.mark.asyncio
    async def test_notification_filtering_and_pagination(self):
        """Test notification filtering by read status and pagination."""
        # Create multiple notifications for the same user
        notifications = [
            {
                "user_id": 1,
                "task_id": f"507f1f77bcf86cd79943901{i}",
                "message": f"Test notification {i}",
                "type": "task_assigned" if i % 2 == 0 else "task_updated"
            }
            for i in range(5)
        ]
        
        created_ids = []
        for notification_data in notifications:
            response = self.client.post("/api/v1/notifications", json=notification_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_ids.append(response.json()["id"])
        
        auth_headers = self.get_auth_headers(user_id=1)
        
        # Mark first two notifications as read
        for notification_id in created_ids[:2]:
            mark_response = self.client.put(
                f"/api/v1/notifications/{notification_id}/read",
                headers=auth_headers
            )
            assert mark_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Test getting all notifications
        all_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        assert all_response.status_code == status.HTTP_200_OK
        all_data = all_response.json()
        assert all_data["total"] == 5
        
        # Test getting only unread notifications
        unread_response = self.client.get(
            "/api/v1/notifications?unread_only=true",
            headers=auth_headers
        )
        assert unread_response.status_code == status.HTTP_200_OK
        unread_data = unread_response.json()
        assert unread_data["total"] == 3  # 3 unread notifications
        
        # Verify all returned notifications are unread
        for notification in unread_data["notifications"]:
            assert notification["is_read"] is False
        
        # Test pagination with limit
        limited_response = self.client.get(
            "/api/v1/notifications?limit=2",
            headers=auth_headers
        )
        assert limited_response.status_code == status.HTTP_200_OK
        limited_data = limited_response.json()
        assert limited_data["total"] == 2
        assert len(limited_data["notifications"]) == 2
    
    @pytest.mark.asyncio
    async def test_mark_all_notifications_as_read_workflow(self):
        """Test marking all notifications as read workflow."""
        # Create multiple unread notifications
        notifications = [
            {
                "user_id": 1,
                "task_id": f"507f1f77bcf86cd79943901{i}",
                "message": f"Unread notification {i}",
                "type": "task_assigned"
            }
            for i in range(3)
        ]
        
        for notification_data in notifications:
            response = self.client.post("/api/v1/notifications", json=notification_data)
            assert response.status_code == status.HTTP_201_CREATED
        
        auth_headers = self.get_auth_headers(user_id=1)
        
        # Verify all notifications are unread
        before_response = self.client.get(
            "/api/v1/notifications?unread_only=true",
            headers=auth_headers
        )
        assert before_response.status_code == status.HTTP_200_OK
        assert before_response.json()["total"] == 3
        
        # Mark all as read
        mark_all_response = self.client.put(
            "/api/v1/notifications/read-all",
            headers=auth_headers
        )
        assert mark_all_response.status_code == status.HTTP_200_OK
        mark_all_data = mark_all_response.json()
        assert mark_all_data["marked_as_read"] == 3
        
        # Verify no unread notifications remain
        after_response = self.client.get(
            "/api/v1/notifications?unread_only=true",
            headers=auth_headers
        )
        assert after_response.status_code == status.HTTP_200_OK
        assert after_response.json()["total"] == 0
        
        # Verify all notifications are now read
        all_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        assert all_response.status_code == status.HTTP_200_OK
        all_data = all_response.json()
        assert all_data["total"] == 3
        for notification in all_data["notifications"]:
            assert notification["is_read"] is True
    
    @pytest.mark.asyncio
    async def test_authentication_and_authorization_flows(self):
        """Test authentication and authorization for protected endpoints."""
        # Create a notification first
        notification_data = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Test notification for auth",
            "type": "task_assigned"
        }
        
        create_response = self.client.post("/api/v1/notifications", json=notification_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        notification_id = create_response.json()["id"]
        
        # Test accessing protected endpoints without authentication
        endpoints_to_test = [
            ("GET", "/api/v1/notifications"),
            ("PUT", f"/api/v1/notifications/{notification_id}/read"),
            ("PUT", "/api/v1/notifications/read-all")
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "PUT":
                response = self.client.put(endpoint)
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test with valid authentication
        auth_headers = self.get_auth_headers(user_id=1)
        
        # Should work with valid auth
        auth_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        assert auth_response.status_code == status.HTTP_200_OK
        
        # Test cross-user authorization (user 2 trying to access user 1's notification)
        user2_headers = self.get_auth_headers(user_id=2, email="user2@example.com")
        
        # User 2 should not see user 1's notifications
        user2_response = self.client.get("/api/v1/notifications", headers=user2_headers)
        assert user2_response.status_code == status.HTTP_200_OK
        user2_data = user2_response.json()
        assert user2_data["total"] == 0  # No notifications for user 2
        
        # User 2 should not be able to mark user 1's notification as read
        cross_user_response = self.client.put(
            f"/api/v1/notifications/{notification_id}/read",
            headers=user2_headers
        )
        assert cross_user_response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_error_handling_and_validation(self):
        """Test error handling and input validation."""
        # Test invalid notification creation data
        invalid_notifications = [
            # Missing required fields
            {
                "user_id": 1,
                "message": "Missing task_id and type"
            },
            # Invalid user_id
            {
                "user_id": 0,
                "task_id": "507f1f77bcf86cd799439011",
                "message": "Invalid user_id",
                "type": "task_assigned"
            },
            # Invalid notification type
            {
                "user_id": 1,
                "task_id": "507f1f77bcf86cd799439011",
                "message": "Invalid type",
                "type": "invalid_type"
            },
            # Empty message
            {
                "user_id": 1,
                "task_id": "507f1f77bcf86cd799439011",
                "message": "",
                "type": "task_assigned"
            }
        ]
        
        for invalid_data in invalid_notifications:
            response = self.client.post("/api/v1/notifications", json=invalid_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid limit parameters
        auth_headers = self.get_auth_headers(user_id=1)
        
        invalid_limits = [0, -1, 101, 1000]
        for limit in invalid_limits:
            response = self.client.get(
                f"/api/v1/notifications?limit={limit}",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test accessing non-existent notification
        response = self.client.put(
            "/api/v1/notifications/99999/read",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint functionality."""
        response = self.client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"
        
        # Health check should not require authentication
        assert "Authorization" not in response.request.headers
    
    @pytest.mark.asyncio
    async def test_database_persistence_and_consistency(self):
        """Test database operations for data persistence and consistency."""
        # Create notification and verify it persists across requests
        notification_data = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Persistence test notification",
            "type": "task_assigned"
        }
        
        create_response = self.client.post("/api/v1/notifications", json=notification_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        created_notification = create_response.json()
        notification_id = created_notification["id"]
        
        # Verify notification exists in multiple requests
        auth_headers = self.get_auth_headers(user_id=1)
        
        for _ in range(3):  # Multiple requests to test consistency
            response = self.client.get("/api/v1/notifications", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 1
            assert data["notifications"][0]["id"] == notification_id
            assert data["notifications"][0]["message"] == "Persistence test notification"
        
        # Test state changes persist
        mark_response = self.client.put(
            f"/api/v1/notifications/{notification_id}/read",
            headers=auth_headers
        )
        assert mark_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify state change persists
        verify_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        assert verify_response.status_code == status.HTTP_200_OK
        verify_data = verify_response.json()
        assert verify_data["notifications"][0]["is_read"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling of concurrent notification operations."""
        # Create a notification
        notification_data = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Concurrent test notification",
            "type": "task_assigned"
        }
        
        create_response = self.client.post("/api/v1/notifications", json=notification_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        notification_id = create_response.json()["id"]
        
        auth_headers = self.get_auth_headers(user_id=1)
        
        # Simulate concurrent read operations
        async def concurrent_read():
            response = self.client.get("/api/v1/notifications", headers=auth_headers)
            return response.status_code == status.HTTP_200_OK
        
        # Run multiple concurrent reads
        tasks = [concurrent_read() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All concurrent operations should succeed
        assert all(results)
        
        # Test concurrent mark as read operations (should be idempotent)
        async def concurrent_mark_read():
            response = self.client.put(
                f"/api/v1/notifications/{notification_id}/read",
                headers=auth_headers
            )
            return response.status_code == status.HTTP_204_NO_CONTENT
        
        # Run multiple concurrent mark as read operations
        mark_tasks = [concurrent_mark_read() for _ in range(3)]
        mark_results = await asyncio.gather(*mark_tasks)
        
        # All operations should succeed (idempotent)
        assert all(mark_results)
        
        # Verify final state is consistent
        final_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        assert final_response.status_code == status.HTTP_200_OK
        final_data = final_response.json()
        assert final_data["notifications"][0]["is_read"] is True


class TestServiceToServiceIntegration:
    """Test service-to-service communication patterns."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    async def test_task_service_notification_creation_simulation(self):
        """Simulate Task Service creating notifications for task events."""
        # Simulate task assignment notification from Task Service
        task_assigned_payload = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "You have been assigned to task 'Implement User Authentication' by John Doe",
            "type": "task_assigned"
        }
        
        response = self.client.post("/api/v1/notifications", json=task_assigned_payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Simulate task status update notification
        task_updated_payload = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Task 'Implement User Authentication' status has been updated to 'in_progress'",
            "type": "task_updated"
        }
        
        response = self.client.post("/api/v1/notifications", json=task_updated_payload)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify both notifications were created
        auth_headers = {"Authorization": f"Bearer {self.create_test_jwt_token(1)}"}
        get_response = self.client.get("/api/v1/notifications", headers=auth_headers)
        
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        assert data["total"] == 2
        
        # Verify notification types
        notification_types = [notif["type"] for notif in data["notifications"]]
        assert "task_assigned" in notification_types
        assert "task_updated" in notification_types
    
    def create_test_jwt_token(self, user_id: int) -> str:
        """Create a test JWT token."""
        return create_jwt_token(user_id, f"user{user_id}@example.com")
    
    @pytest.mark.asyncio
    async def test_bulk_notification_creation_performance(self):
        """Test performance of bulk notification creation."""
        import time
        
        # Create multiple notifications to simulate high load
        notifications = [
            {
                "user_id": i % 3 + 1,  # Distribute across 3 users
                "task_id": f"507f1f77bcf86cd79943901{i:02d}",
                "message": f"Bulk notification {i}",
                "type": "task_assigned" if i % 2 == 0 else "task_updated"
            }
            for i in range(20)
        ]
        
        start_time = time.time()
        
        # Create all notifications
        for notification_data in notifications:
            response = self.client.post("/api/v1/notifications", json=notification_data)
            assert response.status_code == status.HTTP_201_CREATED
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert creation_time < 5.0, f"Bulk creation took {creation_time:.2f}s, expected < 5.0s"
        
        # Verify all notifications were created correctly
        for user_id in [1, 2, 3]:
            auth_headers = {"Authorization": f"Bearer {self.create_test_jwt_token(user_id)}"}
            response = self.client.get("/api/v1/notifications", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            
            # Each user should have some notifications
            data = response.json()
            assert data["total"] > 0