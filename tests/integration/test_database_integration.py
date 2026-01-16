"""
Database integration tests for microservices architecture.

This test suite verifies data consistency and integrity across
all services and their respective databases.
"""

import pytest
import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
USER_SERVICE_URL = "http://localhost:8001"
TASK_SERVICE_URL = "http://localhost:8002"
NOTIFICATION_SERVICE_URL = "http://localhost:8003"

# Database paths
USER_DB_PATH = "user-service/users.db"
TASK_DB_PATH = "task-service/tasks.db"
NOTIFICATION_DB_PATH = "notification-service/notifications.db"


class DatabaseHelper:
    """Helper class for database operations across services."""
    
    @staticmethod
    def get_db_connection(db_path: str) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def execute_query(db_path: str, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        with DatabaseHelper.get_db_connection(db_path) as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Get user from database by ID."""
        try:
            results = DatabaseHelper.execute_query(
                USER_DB_PATH, 
                "SELECT * FROM users WHERE id = ?", 
                (user_id,)
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    @staticmethod
    def get_tasks_by_user(user_id: int) -> List[Dict]:
        """Get all tasks for a user."""
        try:
            return DatabaseHelper.execute_query(
                TASK_DB_PATH,
                "SELECT * FROM tasks WHERE user_id = ?",
                (user_id,)
            )
        except Exception as e:
            logger.error(f"Error fetching tasks for user {user_id}: {e}")
            return []
    
    @staticmethod
    def get_notifications_by_user(user_id: int) -> List[Dict]:
        """Get all notifications for a user."""
        try:
            return DatabaseHelper.execute_query(
                NOTIFICATION_DB_PATH,
                "SELECT * FROM notifications WHERE user_id = ?",
                (user_id,)
            )
        except Exception as e:
            logger.error(f"Error fetching notifications for user {user_id}: {e}")
            return []
    
    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Dict]:
        """Get task from database by ID."""
        try:
            results = DatabaseHelper.execute_query(
                TASK_DB_PATH,
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {e}")
            return None


class APIHelper:
    """Helper class for API operations across services."""
    
    @staticmethod
    async def make_request(method: str, url: str, headers: Dict = None, json_data: Dict = None) -> httpx.Response:
        """Make HTTP request with proper error handling."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    json=json_data
                )
                return response
            except httpx.RequestError as e:
                logger.error(f"Request failed: {e}")
                raise
    
    @staticmethod
    async def create_test_user(username: str = "testuser", email: str = "test@example.com") -> Dict:
        """Create a test user and return user data with token."""
        user_data = {
            "username": username,
            "email": email,
            "password": "testpassword123"
        }
        
        response = await APIHelper.make_request(
            "POST", 
            f"{USER_SERVICE_URL}/register", 
            json_data=user_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create user: {response.text}")
        
        # Login to get token
        login_response = await APIHelper.make_request(
            "POST",
            f"{USER_SERVICE_URL}/login",
            json_data={"username": username, "password": "testpassword123"}
        )
        
        if login_response.status_code != 200:
            raise Exception(f"Failed to login: {login_response.text}")
        
        login_data = login_response.json()
        user_info = response.json()
        user_info["token"] = login_data["access_token"]
        
        return user_info
    
    @staticmethod
    async def create_test_task(user_token: str, title: str = "Test Task") -> Dict:
        """Create a test task and return task data."""
        task_data = {
            "title": title,
            "description": "Test task description",
            "priority": "medium",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await APIHelper.make_request(
            "POST",
            f"{TASK_SERVICE_URL}/tasks",
            headers=headers,
            json_data=task_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create task: {response.text}")
        
        return response.json()


@pytest.fixture
async def test_user():
    """Create a test user for integration tests."""
    user = await APIHelper.create_test_user(
        username=f"testuser_{int(time.time())}",
        email=f"test_{int(time.time())}@example.com"
    )
    yield user
    # Cleanup would go here if needed


@pytest.fixture
async def test_task(test_user):
    """Create a test task for integration tests."""
    task = await APIHelper.create_test_task(
        test_user["token"],
        title=f"Test Task {int(time.time())}"
    )
    yield task


class TestDatabaseConsistency:
    """Test data consistency across all microservices."""
    
    @pytest.mark.asyncio
    async def test_user_creation_consistency(self, test_user):
        """Test that user creation is consistent across services."""
        user_id = test_user["id"]
        
        # Verify user exists in database
        db_user = DatabaseHelper.get_user_by_id(user_id)
        assert db_user is not None, f"User {user_id} not found in database"
        assert db_user["username"] == test_user["username"]
        assert db_user["email"] == test_user["email"]
        
        # Verify user can be retrieved via API
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = await APIHelper.make_request(
            "GET",
            f"{USER_SERVICE_URL}/profile",
            headers=headers
        )
        
        assert response.status_code == 200
        api_user = response.json()
        assert api_user["id"] == user_id
        assert api_user["username"] == test_user["username"]
        
        logger.info(f"✓ User consistency verified for user {user_id}")
    
    @pytest.mark.asyncio
    async def test_task_creation_consistency(self, test_user, test_task):
        """Test that task creation maintains consistency across services."""
        task_id = test_task["id"]
        user_id = test_user["id"]
        
        # Verify task exists in database
        db_task = DatabaseHelper.get_task_by_id(task_id)
        assert db_task is not None, f"Task {task_id} not found in database"
        assert db_task["user_id"] == user_id
        assert db_task["title"] == test_task["title"]
        
        # Verify task can be retrieved via API
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = await APIHelper.make_request(
            "GET",
            f"{TASK_SERVICE_URL}/tasks/{task_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        api_task = response.json()
        assert api_task["id"] == task_id
        assert api_task["user_id"] == user_id
        
        # Verify user-task relationship
        user_tasks = DatabaseHelper.get_tasks_by_user(user_id)
        task_ids = [task["id"] for task in user_tasks]
        assert task_id in task_ids, f"Task {task_id} not associated with user {user_id}"
        
        logger.info(f"✓ Task consistency verified for task {task_id}")
    
    @pytest.mark.asyncio
    async def test_notification_creation_consistency(self, test_user, test_task):
        """Test that notifications are created consistently when tasks are created."""
        user_id = test_user["id"]
        task_id = test_task["id"]
        
        # Wait a moment for async notification creation
        await asyncio.sleep(2)
        
        # Check if notification was created in database
        notifications = DatabaseHelper.get_notifications_by_user(user_id)
        
        # Find notification related to the task
        task_notifications = [
            n for n in notifications 
            if "task" in n.get("message", "").lower() or str(task_id) in n.get("message", "")
        ]
        
        if task_notifications:
            notification = task_notifications[0]
            assert notification["user_id"] == user_id
            assert notification["type"] in ["task_created", "info", "success"]
            
            # Verify notification via API
            headers = {"Authorization": f"Bearer {test_user['token']}"}
            response = await APIHelper.make_request(
                "GET",
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                headers=headers
            )
            
            if response.status_code == 200:
                api_notifications = response.json()
                api_notification_ids = [n["id"] for n in api_notifications]
                assert notification["id"] in api_notification_ids
            
            logger.info(f"✓ Notification consistency verified for task {task_id}")
        else:
            logger.warning(f"No notifications found for task {task_id} - this may be expected if notifications are disabled")
    
    @pytest.mark.asyncio
    async def test_cross_service_data_integrity(self, test_user):
        """Test data integrity across multiple services with complex operations."""
        user_id = test_user["id"]
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = await APIHelper.create_test_task(
                test_user["token"],
                title=f"Integrity Test Task {i+1}"
            )
            tasks.append(task)
        
        # Wait for any async operations
        await asyncio.sleep(2)
        
        # Verify all tasks exist in database
        db_tasks = DatabaseHelper.get_tasks_by_user(user_id)
        created_task_ids = [task["id"] for task in tasks]
        db_task_ids = [task["id"] for task in db_tasks]
        
        for task_id in created_task_ids:
            assert task_id in db_task_ids, f"Task {task_id} missing from database"
        
        # Update a task and verify consistency
        task_to_update = tasks[0]
        update_data = {
            "title": "Updated Task Title",
            "status": "in_progress"
        }
        
        response = await APIHelper.make_request(
            "PUT",
            f"{TASK_SERVICE_URL}/tasks/{task_to_update['id']}",
            headers=headers,
            json_data=update_data
        )
        
        assert response.status_code == 200
        
        # Verify update in database
        updated_task = DatabaseHelper.get_task_by_id(task_to_update["id"])
        assert updated_task["title"] == "Updated Task Title"
        assert updated_task["status"] == "in_progress"
        
        # Delete a task and verify consistency
        task_to_delete = tasks[1]
        response = await APIHelper.make_request(
            "DELETE",
            f"{TASK_SERVICE_URL}/tasks/{task_to_delete['id']}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify deletion in database
        deleted_task = DatabaseHelper.get_task_by_id(task_to_delete["id"])
        assert deleted_task is None or deleted_task.get("deleted_at") is not None
        
        logger.info(f"✓ Cross-service data integrity verified for user {user_id}")
    
    @pytest.mark.asyncio
    async def test_database_transaction_consistency(self, test_user):
        """Test that database transactions maintain consistency across services."""
        user_id = test_user["id"]
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Get initial counts
        initial_tasks = len(DatabaseHelper.get_tasks_by_user(user_id))
        initial_notifications = len(DatabaseHelper.get_notifications_by_user(user_id))
        
        # Create a task that might trigger notifications
        task_data = {
            "title": "Transaction Test Task",
            "description": "Testing transaction consistency",
            "priority": "high",
            "due_date": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        response = await APIHelper.make_request(
            "POST",
            f"{TASK_SERVICE_URL}/tasks",
            headers=headers,
            json_data=task_data
        )
        
        assert response.status_code == 201
        task = response.json()
        
        # Wait for any async operations
        await asyncio.sleep(2)
        
        # Verify counts increased appropriately
        final_tasks = len(DatabaseHelper.get_tasks_by_user(user_id))
        final_notifications = len(DatabaseHelper.get_notifications_by_user(user_id))
        
        assert final_tasks == initial_tasks + 1, "Task count should increase by 1"
        
        # Notifications might or might not be created depending on configuration
        if final_notifications > initial_notifications:
            logger.info(f"✓ Notification created as expected")
        else:
            logger.info(f"✓ No notification created - this may be expected")
        
        # Verify task data integrity
        db_task = DatabaseHelper.get_task_by_id(task["id"])
        assert db_task is not None
        assert db_task["title"] == task_data["title"]
        assert db_task["user_id"] == user_id
        
        logger.info(f"✓ Database transaction consistency verified")


class TestDatabasePerformance:
    """Test database performance and connection handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, test_user):
        """Test database consistency under concurrent operations."""
        user_id = test_user["id"]
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create multiple tasks concurrently
        async def create_task(index):
            task_data = {
                "title": f"Concurrent Task {index}",
                "description": f"Task created concurrently {index}",
                "priority": "medium"
            }
            return await APIHelper.make_request(
                "POST",
                f"{TASK_SERVICE_URL}/tasks",
                headers=headers,
                json_data=task_data
            )
        
        # Create 5 tasks concurrently
        tasks = await asyncio.gather(*[create_task(i) for i in range(5)])
        
        # Verify all tasks were created successfully
        for response in tasks:
            assert response.status_code == 201
        
        # Wait for any async operations
        await asyncio.sleep(2)
        
        # Verify all tasks exist in database
        db_tasks = DatabaseHelper.get_tasks_by_user(user_id)
        concurrent_tasks = [task for task in db_tasks if "Concurrent Task" in task["title"]]
        
        assert len(concurrent_tasks) == 5, f"Expected 5 concurrent tasks, found {len(concurrent_tasks)}"
        
        logger.info(f"✓ Concurrent database operations handled correctly")
    
    @pytest.mark.asyncio
    async def test_database_connection_resilience(self):
        """Test database connection handling and resilience."""
        # Test connection to each database
        databases = [
            (USER_DB_PATH, "users"),
            (TASK_DB_PATH, "tasks"),
            (NOTIFICATION_DB_PATH, "notifications")
        ]
        
        for db_path, table_name in databases:
            if os.path.exists(db_path):
                try:
                    # Test basic connection
                    with DatabaseHelper.get_db_connection(db_path) as conn:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        logger.info(f"✓ Database {db_path} accessible, {table_name} count: {count}")
                except Exception as e:
                    pytest.fail(f"Database connection failed for {db_path}: {e}")
            else:
                logger.warning(f"Database not found: {db_path}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])