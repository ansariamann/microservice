"""
Test data factories for creating consistent test data across all services.

This module provides factory functions for generating test data that can be
used across unit tests, integration tests, and end-to-end tests.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid


@dataclass
class TestUser:
    """Test user data structure."""
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    password: str = ""
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class TestTask:
    """Test task data structure."""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    due_date: Optional[datetime] = None
    status: str = "to_do"
    creator_id: Optional[int] = None
    assignee_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class TestNotification:
    """Test notification data structure."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    task_id: Optional[str] = None
    message: str = ""
    type: str = "task_assigned"
    is_read: bool = False
    created_at: Optional[datetime] = None


class TestDataFactory:
    """Factory class for generating test data."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string of specified length."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = TestDataFactory.random_string(8).lower()
        domain = random.choice(['example.com', 'test.org', 'demo.net'])
        return f"{username}@{domain}"
    
    @staticmethod
    def random_name() -> str:
        """Generate a random full name."""
        first_names = ['John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    @staticmethod
    def future_datetime(days_ahead: int = 7) -> datetime:
        """Generate a future datetime."""
        return datetime.now() + timedelta(days=random.randint(1, days_ahead))
    
    @staticmethod
    def past_datetime(days_back: int = 30) -> datetime:
        """Generate a past datetime."""
        return datetime.now() - timedelta(days=random.randint(1, days_back))


class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_user(
        email: Optional[str] = None,
        name: Optional[str] = None,
        password: str = "testpassword123",
        **kwargs
    ) -> TestUser:
        """Create a test user with optional custom fields."""
        return TestUser(
            email=email or TestDataFactory.random_email(),
            name=name or TestDataFactory.random_name(),
            password=password,
            created_at=kwargs.get('created_at', datetime.now()),
            updated_at=kwargs.get('updated_at', datetime.now()),
            **{k: v for k, v in kwargs.items() if k not in ['created_at', 'updated_at']}
        )
    
    @staticmethod
    def create_users(count: int, **kwargs) -> List[TestUser]:
        """Create multiple test users."""
        return [UserFactory.create_user(**kwargs) for _ in range(count)]
    
    @staticmethod
    def create_user_dict(
        email: Optional[str] = None,
        name: Optional[str] = None,
        password: str = "testpassword123"
    ) -> Dict[str, Any]:
        """Create a user dictionary for API requests."""
        return {
            "email": email or TestDataFactory.random_email(),
            "name": name or TestDataFactory.random_name(),
            "password": password
        }
    
    @staticmethod
    def create_login_dict(email: str, password: str = "testpassword123") -> Dict[str, str]:
        """Create a login dictionary for API requests."""
        return {
            "email": email,
            "password": password
        }


class TaskFactory:
    """Factory for creating test tasks."""
    
    @staticmethod
    def create_task(
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: str = "to_do",
        creator_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        **kwargs
    ) -> TestTask:
        """Create a test task with optional custom fields."""
        return TestTask(
            title=title or f"Test Task {TestDataFactory.random_string(5)}",
            description=description or f"Test task description {TestDataFactory.random_string(10)}",
            due_date=due_date or TestDataFactory.future_datetime(),
            status=status,
            creator_id=creator_id,
            assignee_id=assignee_id,
            created_at=kwargs.get('created_at', datetime.now()),
            updated_at=kwargs.get('updated_at', datetime.now()),
            **{k: v for k, v in kwargs.items() if k not in ['created_at', 'updated_at']}
        )
    
    @staticmethod
    def create_tasks(count: int, **kwargs) -> List[TestTask]:
        """Create multiple test tasks."""
        return [TaskFactory.create_task(**kwargs) for _ in range(count)]
    
    @staticmethod
    def create_task_dict(
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a task dictionary for API requests."""
        task_dict = {
            "title": title or f"Test Task {TestDataFactory.random_string(5)}",
            "description": description or f"Test task description {TestDataFactory.random_string(10)}",
        }
        
        if due_date:
            task_dict["due_date"] = due_date
        else:
            task_dict["due_date"] = TestDataFactory.future_datetime().isoformat()
        
        if assignee_id:
            task_dict["assignee_id"] = assignee_id
            
        return task_dict
    
    @staticmethod
    def create_task_update_dict(
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a task update dictionary for API requests."""
        update_dict = {}
        
        if title:
            update_dict["title"] = title
        if description:
            update_dict["description"] = description
        if status:
            update_dict["status"] = status
        if assignee_id:
            update_dict["assignee_id"] = assignee_id
            
        return update_dict


class NotificationFactory:
    """Factory for creating test notifications."""
    
    @staticmethod
    def create_notification(
        user_id: Optional[int] = None,
        task_id: Optional[str] = None,
        message: Optional[str] = None,
        notification_type: str = "task_assigned",
        is_read: bool = False,
        **kwargs
    ) -> TestNotification:
        """Create a test notification with optional custom fields."""
        return TestNotification(
            user_id=user_id or random.randint(1, 100),
            task_id=task_id or str(uuid.uuid4()),
            message=message or f"Test notification message {TestDataFactory.random_string(5)}",
            type=notification_type,
            is_read=is_read,
            created_at=kwargs.get('created_at', datetime.now()),
            **{k: v for k, v in kwargs.items() if k != 'created_at'}
        )
    
    @staticmethod
    def create_notifications(count: int, **kwargs) -> List[TestNotification]:
        """Create multiple test notifications."""
        return [NotificationFactory.create_notification(**kwargs) for _ in range(count)]
    
    @staticmethod
    def create_notification_dict(
        user_id: int,
        task_id: str,
        message: Optional[str] = None,
        notification_type: str = "task_assigned"
    ) -> Dict[str, Any]:
        """Create a notification dictionary for API requests."""
        return {
            "user_id": user_id,
            "task_id": task_id,
            "message": message or f"Test notification message {TestDataFactory.random_string(5)}",
            "type": notification_type
        }


class ScenarioFactory:
    """Factory for creating complex test scenarios."""
    
    @staticmethod
    def create_user_with_tasks_scenario(
        task_count: int = 3,
        assigned_task_count: int = 2
    ) -> Dict[str, Any]:
        """Create a scenario with a user and their tasks."""
        user = UserFactory.create_user()
        assignee = UserFactory.create_user()
        
        # Tasks created by the user
        created_tasks = TaskFactory.create_tasks(
            task_count, 
            creator_id=1,  # Will be set to actual user ID in tests
            assignee_id=2   # Will be set to actual assignee ID in tests
        )
        
        # Tasks assigned to the user
        assigned_tasks = TaskFactory.create_tasks(
            assigned_task_count,
            creator_id=2,   # Will be set to actual creator ID in tests
            assignee_id=1   # Will be set to actual user ID in tests
        )
        
        return {
            "user": user,
            "assignee": assignee,
            "created_tasks": created_tasks,
            "assigned_tasks": assigned_tasks
        }
    
    @staticmethod
    def create_notification_scenario(
        user_count: int = 2,
        notifications_per_user: int = 3
    ) -> Dict[str, Any]:
        """Create a scenario with users and their notifications."""
        users = UserFactory.create_users(user_count)
        notifications = {}
        
        for i, user in enumerate(users):
            user_notifications = NotificationFactory.create_notifications(
                notifications_per_user,
                user_id=i + 1  # Will be set to actual user ID in tests
            )
            notifications[f"user_{i + 1}"] = user_notifications
        
        return {
            "users": users,
            "notifications": notifications
        }


# Convenience functions for quick test data creation
def create_test_user(**kwargs) -> TestUser:
    """Quick function to create a test user."""
    return UserFactory.create_user(**kwargs)


def create_test_task(**kwargs) -> TestTask:
    """Quick function to create a test task."""
    return TaskFactory.create_task(**kwargs)


def create_test_notification(**kwargs) -> TestNotification:
    """Quick function to create a test notification."""
    return NotificationFactory.create_notification(**kwargs)


# Export commonly used classes and functions
__all__ = [
    'TestUser', 'TestTask', 'TestNotification',
    'TestDataFactory', 'UserFactory', 'TaskFactory', 'NotificationFactory', 'ScenarioFactory',
    'create_test_user', 'create_test_task', 'create_test_notification'
]