"""
Basic functionality test for notification service endpoints.
This script tests the notification service API endpoints manually.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_database

def test_basic_functionality():
    """Test basic notification service functionality."""
    print("Testing Notification Service Basic Functionality")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Health check
    print("1. Testing health check endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✓ Health check passed")
    
    # Test 2: Create notification (internal endpoint - no auth required)
    print("\n2. Testing notification creation endpoint...")
    notification_data = {
        "user_id": 1,
        "task_id": "507f1f77bcf86cd799439011",
        "message": "You have been assigned to task 'Test Task' by John Doe",
        "type": "task_assigned"
    }
    response = client.post("/api/v1/notifications", json=notification_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print(f"   Response: {response.json()}")
        print("   ✓ Notification creation passed")
    else:
        print(f"   Error: {response.text}")
        print("   ✗ Notification creation failed")
    
    # Test 3: Get notifications without auth (should fail)
    print("\n3. Testing get notifications without auth...")
    response = client.get("/api/v1/notifications")
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print("   ✓ Authentication required (as expected)")
    else:
        print(f"   Unexpected status: {response.status_code}")
    
    # Test 4: Test invalid notification type
    print("\n4. Testing invalid notification type...")
    invalid_data = {
        "user_id": 1,
        "task_id": "507f1f77bcf86cd799439011",
        "message": "Test message",
        "type": "invalid_type"
    }
    response = client.post("/api/v1/notifications", json=invalid_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 422:
        print("   ✓ Validation error (as expected)")
    else:
        print(f"   Unexpected status: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Basic functionality tests completed!")

if __name__ == "__main__":
    test_basic_functionality()