#!/usr/bin/env python3
"""
Basic functionality test for Task Service.
Tests core endpoints without requiring MongoDB.
"""

from fastapi.testclient import TestClient
from app.main import app

def test_basic_functionality():
    """Test basic Task Service functionality."""
    client = TestClient(app)
    
    print("Testing Task Service Basic Functionality")
    print("=" * 50)
    
    # Test health check
    print("1. Testing health check endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "task-service"}
    print("   ✓ Health check passed")
    
    # Test OpenAPI documentation
    print("2. Testing OpenAPI documentation...")
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Task Service"
    assert schema["info"]["version"] == "1.0.0"
    print("   ✓ OpenAPI documentation available")
    
    # Test Swagger docs
    print("3. Testing Swagger documentation...")
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    print("   ✓ Swagger docs available")
    
    # Test ReDoc
    print("4. Testing ReDoc documentation...")
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    print("   ✓ ReDoc documentation available")
    
    # Test authentication requirement
    print("5. Testing authentication requirement...")
    response = client.get("/api/v1/tasks")
    # Accept either 401 or 403 as both indicate authentication/authorization failure
    assert response.status_code in [401, 403]
    print(f"   ✓ Authentication required for protected endpoints (status: {response.status_code})")
    
    # Test invalid authentication
    print("6. Testing invalid authentication...")
    headers = {"Authorization": "Bearer invalid.token"}
    response = client.get("/api/v1/tasks", headers=headers)
    assert response.status_code in [401, 403]
    print(f"   ✓ Invalid tokens rejected (status: {response.status_code})")
    
    print("\n" + "=" * 50)
    print("All basic functionality tests passed! ✓")
    print("Task Service is ready for deployment.")

if __name__ == "__main__":
    test_basic_functionality()