"""
End-to-end integration tests for authentication flow across all services.

This test suite demonstrates how authentication works across the entire
microservices architecture, testing the complete user journey from
registration to task management with notifications.
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class TestEndToEndAuthFlow:
    """End-to-end integration tests for authentication across services."""
    
    def __init__(self):
        self.user_service_url = "http://localhost:8001"
        self.task_service_url = "http://localhost:8002"
        self.notification_service_url = "http://localhost:8003"
        self.test_user_data = {
            "email": "integration.test@example.com",
            "password": "TestPassword123!",
            "name": "Integration Test User"
        }
        self.auth_token: Optional[str] = None
        self.user_id: Optional[int] = None
    
    async def setup_method(self):
        """Set up test environment."""
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'client'):
            await self.client.aclose()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with JWT token."""
        if not self.auth_token:
            raise ValueError("No auth token available. Please login first.")
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    @pytest.mark.asyncio
    async def test_complete_user_journey_with_authentication(self):
        """Test complete user journey from registration to task management."""
        
        # Step 1: User Registration
        print("Step 1: Testing user registration...")
        registration_response = await self.client.post(
            f"{self.user_service_url}/api/v1/register",
            json=self.test_user_data
        )
        
        assert registration_response.status_code == 201
        registration_data = registration_response.json()
        assert "access_token" in registration_data
        assert registration_data["user"]["email"] == self.test_user_data["email"]
        
        # Store auth token and user ID
        self.auth_token = registration_data["access_token"]
        self.user_id = registration_data["user"]["id"]
        print(f"✓ User registered successfully with ID: {self.user_id}")
        
        # Step 2: User Login (verify token works)
        print("Step 2: Testing user login...")
        login_response = await self.client.post(
            f"{self.user_service_url}/api/v1/login",
            json={
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        
        # Update auth token with fresh one from login
        self.auth_token = login_data["access_token"]
        print("✓ User login successful")
        
        # Step 3: Access User Profile (test JWT validation)
        print("Step 3: Testing profile access with JWT...")
        profile_response = await self.client.get(
            f"{self.user_service_url}/api/v1/profile",
            headers=self.get_auth_headers()
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == self.test_user_data["email"]
        assert profile_data["id"] == self.user_id
        print("✓ Profile access with JWT successful")
        
        # Step 4: Create Task (test cross-service JWT validation)
        print("Step 4: Testing task creation with JWT...")
        task_data = {
            "title": "Integration Test Task",
            "description": "This task tests end-to-end authentication flow",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "to_do"
        }
        
        task_response = await self.client.post(
            f"{self.task_service_url}/api/v1/tasks",
            json=task_data,
            headers=self.get_auth_headers()
        )
        
        assert task_response.status_code == 201
        task_response_data = task_response.json()
        assert task_response_data["title"] == task_data["title"]
        assert task_response_data["creator_id"] == self.user_id
        task_id = task_response_data["id"]
        print(f"✓ Task created successfully with ID: {task_id}")
        
        # Step 5: Retrieve Tasks (test JWT validation in Task Service)
        print("Step 5: Testing task retrieval with JWT...")
        tasks_response = await self.client.get(
            f"{self.task_service_url}/api/v1/tasks",
            headers=self.get_auth_headers()
        )
        
        assert tasks_response.status_code == 200
        tasks_data = tasks_response.json()
        assert len(tasks_data) >= 1
        assert any(task["id"] == task_id for task in tasks_data)
        print("✓ Task retrieval with JWT successful")
        
        # Step 6: Update Task Status (test JWT validation and notification trigger)
        print("Step 6: Testing task status update with JWT...")
        status_update_response = await self.client.put(
            f"{self.task_service_url}/api/v1/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=self.get_auth_headers()
        )
        
        assert status_update_response.status_code == 200
        updated_task = status_update_response.json()
        assert updated_task["status"] == "in_progress"
        print("✓ Task status update with JWT successful")
        
        # Step 7: Check Notifications (test JWT validation in Notification Service)
        print("Step 7: Testing notification retrieval with JWT...")
        # Wait a moment for notification to be created
        await asyncio.sleep(1)
        
        notifications_response = await self.client.get(
            f"{self.notification_service_url}/api/v1/notifications",
            headers=self.get_auth_headers()
        )
        
        assert notifications_response.status_code == 200
        notifications_data = notifications_response.json()
        print(f"✓ Notification retrieval with JWT successful. Found {len(notifications_data)} notifications")
        
        # Step 8: Test Invalid Token (security validation)
        print("Step 8: Testing invalid token rejection...")
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        
        invalid_response = await self.client.get(
            f"{self.user_service_url}/api/v1/profile",
            headers=invalid_headers
        )
        
        assert invalid_response.status_code == 401
        print("✓ Invalid token properly rejected")
        
        # Step 9: Test No Token (security validation)
        print("Step 9: Testing no token rejection...")
        no_token_response = await self.client.get(
            f"{self.task_service_url}/api/v1/tasks"
        )
        
        assert no_token_response.status_code == 401
        print("✓ Missing token properly rejected")
        
        print("\n🎉 Complete end-to-end authentication flow test passed!")
    
    @pytest.mark.asyncio
    async def test_cross_service_jwt_consistency(self):
        """Test that JWT tokens work consistently across all services."""
        
        # First register and login to get a token
        registration_response = await self.client.post(
            f"{self.user_service_url}/api/v1/register",
            json={
                "email": "jwt.test@example.com",
                "password": "TestPassword123!",
                "name": "JWT Test User"
            }
        )
        
        assert registration_response.status_code == 201
        auth_data = registration_response.json()
        token = auth_data["access_token"]
        user_id = auth_data["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test token validation across all services
        services_to_test = [
            (self.user_service_url, "/api/v1/profile"),
            (self.task_service_url, "/api/v1/tasks"),
            (self.notification_service_url, "/api/v1/notifications")
        ]
        
        for service_url, endpoint in services_to_test:
            print(f"Testing JWT validation on {service_url}{endpoint}")
            
            response = await self.client.get(
                f"{service_url}{endpoint}",
                headers=headers
            )
            
            # All services should accept the same JWT token
            assert response.status_code in [200, 201], f"Service {service_url} rejected valid JWT token"
            print(f"✓ JWT token accepted by {service_url}")
        
        print("✓ JWT token consistency across all services verified")
    
    @pytest.mark.asyncio
    async def test_service_to_service_communication_with_auth(self):
        """Test that services can communicate with each other properly."""
        
        # Register two users for task assignment testing
        user1_data = {
            "email": "user1.comm@example.com",
            "password": "TestPassword123!",
            "name": "User One"
        }
        
        user2_data = {
            "email": "user2.comm@example.com", 
            "password": "TestPassword123!",
            "name": "User Two"
        }
        
        # Register both users
        user1_response = await self.client.post(
            f"{self.user_service_url}/api/v1/register",
            json=user1_data
        )
        
        user2_response = await self.client.post(
            f"{self.user_service_url}/api/v1/register",
            json=user2_data
        )
        
        assert user1_response.status_code == 201
        assert user2_response.status_code == 201
        
        user1_auth = user1_response.json()
        user2_auth = user2_response.json()
        
        user1_token = user1_auth["access_token"]
        user1_id = user1_auth["user"]["id"]
        user2_id = user2_auth["user"]["id"]
        
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User 1 creates a task
        task_data = {
            "title": "Service Communication Test Task",
            "description": "Testing service-to-service communication",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "assignee_id": user2_id  # Assign to user 2
        }
        
        task_response = await self.client.post(
            f"{self.task_service_url}/api/v1/tasks",
            json=task_data,
            headers=user1_headers
        )
        
        assert task_response.status_code == 201
        task_data_response = task_response.json()
        task_id = task_data_response["id"]
        
        print(f"✓ Task created and assigned. Task ID: {task_id}")
        
        # Wait for notification to be created via service-to-service communication
        await asyncio.sleep(2)
        
        # Check that user 2 received a notification about the task assignment
        user2_token = user2_auth["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        notifications_response = await self.client.get(
            f"{self.notification_service_url}/api/v1/notifications",
            headers=user2_headers
        )
        
        assert notifications_response.status_code == 200
        notifications = notifications_response.json()
        
        # Should have at least one notification about task assignment
        assignment_notifications = [
            n for n in notifications 
            if n["type"] == "task_assigned" and task_id in n["message"]
        ]
        
        assert len(assignment_notifications) > 0, "No task assignment notification found"
        print("✓ Service-to-service communication working: Task Service → Notification Service")
        
        # Update task status to trigger another notification
        status_update_response = await self.client.put(
            f"{self.task_service_url}/api/v1/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=user2_headers  # User 2 updates the task
        )
        
        assert status_update_response.status_code == 200
        
        # Wait for status update notification
        await asyncio.sleep(2)
        
        # Check for status update notification
        updated_notifications_response = await self.client.get(
            f"{self.notification_service_url}/api/v1/notifications",
            headers=user1_headers  # User 1 should get notification about status change
        )
        
        assert updated_notifications_response.status_code == 200
        updated_notifications = updated_notifications_response.json()
        
        status_notifications = [
            n for n in updated_notifications 
            if n["type"] == "task_updated" and task_id in n["message"]
        ]
        
        assert len(status_notifications) > 0, "No task status update notification found"
        print("✓ Service-to-service communication working: Task status updates trigger notifications")
        
        print("\n🎉 Service-to-service communication with authentication test passed!")


if __name__ == "__main__":
    """
    Run integration tests manually.
    
    Note: This requires all services to be running:
    - User Service on port 8001
    - Task Service on port 8002  
    - Notification Service on port 8003
    
    Start services with: docker-compose up
    Then run: python tests/integration/test_end_to_end_auth_flow.py
    """
    import asyncio
    
    async def run_tests():
        test_instance = TestEndToEndAuthFlow()
        
        try:
            await test_instance.setup_method()
            
            print("🚀 Starting End-to-End Authentication Flow Tests")
            print("=" * 60)
            
            await test_instance.test_complete_user_journey_with_authentication()
            print("\n" + "=" * 60)
            
            await test_instance.test_cross_service_jwt_consistency()
            print("\n" + "=" * 60)
            
            await test_instance.test_service_to_service_communication_with_auth()
            
            print("\n" + "=" * 60)
            print("🎉 All integration tests passed successfully!")
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            raise
        finally:
            await test_instance.teardown_method()
    
    asyncio.run(run_tests())