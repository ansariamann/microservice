"""
Pytest configuration for integration tests.

This file contains shared fixtures and configuration for all integration tests.
"""

import pytest
import asyncio
import httpx
import time
import logging
from typing import Dict, List

# Configure logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service URLs
USER_SERVICE_URL = "http://localhost:8001"
TASK_SERVICE_URL = "http://localhost:8002"
NOTIFICATION_SERVICE_URL = "http://localhost:8003"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client():
    """Provide an HTTP client for making requests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def service_health_check(http_client):
    """Check that all services are running before tests."""
    services = [
        ("User Service", USER_SERVICE_URL),
        ("Task Service", TASK_SERVICE_URL),
        ("Notification Service", NOTIFICATION_SERVICE_URL)
    ]
    
    for service_name, url in services:
        try:
            response = await http_client.get(f"{url}/health")
            if response.status_code != 200:
                pytest.skip(f"{service_name} is not healthy (status: {response.status_code})")
        except httpx.RequestError:
            pytest.skip(f"{service_name} is not accessible at {url}")
    
    return True


@pytest.fixture
async def clean_test_user(http_client):
    """Create a clean test user for each test."""
    timestamp = int(time.time())
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    response = await http_client.post(
        f"{USER_SERVICE_URL}/register",
        json=user_data
    )
    
    if response.status_code != 201:
        pytest.fail(f"Failed to create test user: {response.text}")
    
    # Login to get token
    login_response = await http_client.post(
        f"{USER_SERVICE_URL}/login",
        json={"username": user_data["username"], "password": user_data["password"]}
    )
    
    if login_response.status_code != 200:
        pytest.fail(f"Failed to login test user: {login_response.text}")
    
    user_info = response.json()
    login_data = login_response.json()
    user_info["token"] = login_data["access_token"]
    user_info["password"] = user_data["password"]
    
    yield user_info
    
    # Cleanup could be added here if needed


@pytest.fixture
async def multiple_test_users(http_client):
    """Create multiple test users for interaction testing."""
    users = []
    timestamp = int(time.time())
    
    for i in range(3):
        user_data = {
            "username": f"testuser_{i}_{timestamp}",
            "email": f"test_{i}_{timestamp}@example.com",
            "password": "testpassword123"
        }
        
        # Register user
        response = await http_client.post(
            f"{USER_SERVICE_URL}/register",
            json=user_data
        )
        
        if response.status_code != 201:
            pytest.fail(f"Failed to create test user {i}: {response.text}")
        
        # Login to get token
        login_response = await http_client.post(
            f"{USER_SERVICE_URL}/login",
            json={"username": user_data["username"], "password": user_data["password"]}
        )
        
        if login_response.status_code != 200:
            pytest.fail(f"Failed to login test user {i}: {login_response.text}")
        
        user_info = response.json()
        login_data = login_response.json()
        user_info["token"] = login_data["access_token"]
        user_info["password"] = user_data["password"]
        
        users.append(user_info)
    
    yield users
    
    # Cleanup could be added here if needed


@pytest.fixture
def auth_headers():
    """Helper function to create auth headers."""
    def _auth_headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers


@pytest.fixture
async def sample_task_data():
    """Provide sample task data for testing."""
    return {
        "title": "Integration Test Task",
        "description": "This is a test task for integration testing",
        "priority": "medium",
        "due_date": "2024-12-31T23:59:59Z"
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might take longer
        if any(keyword in item.name.lower() for keyword in ["concurrent", "performance", "lifecycle"]):
            item.add_marker(pytest.mark.slow)


# Custom assertions for integration tests
def assert_valid_response(response: httpx.Response, expected_status: int = 200):
    """Assert that a response is valid and has expected status."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_valid_json_response(response: httpx.Response, expected_status: int = 200):
    """Assert that a response is valid JSON with expected status."""
    assert_valid_response(response, expected_status)
    try:
        response.json()
    except ValueError:
        pytest.fail(f"Response is not valid JSON: {response.text}")


def assert_notification_exists(notifications: List[Dict], notification_type: str = None, message_contains: str = None):
    """Assert that a specific notification exists in the list."""
    matching_notifications = notifications
    
    if notification_type:
        matching_notifications = [n for n in matching_notifications if n.get("type") == notification_type]
    
    if message_contains:
        matching_notifications = [n for n in matching_notifications if message_contains.lower() in n.get("message", "").lower()]
    
    assert len(matching_notifications) > 0, f"No matching notifications found. Available: {[n.get('type') for n in notifications]}"


# Export commonly used functions
__all__ = [
    "USER_SERVICE_URL",
    "TASK_SERVICE_URL", 
    "NOTIFICATION_SERVICE_URL",
    "assert_valid_response",
    "assert_valid_json_response",
    "assert_notification_exists"
]