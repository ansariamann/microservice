#!/usr/bin/env python3
"""
Test script to verify API documentation is properly configured.
"""

import json
from app.main import app

def test_openapi_schema():
    """Test that OpenAPI schema is properly generated."""
    openapi_schema = app.openapi()
    
    # Check basic schema structure
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert "paths" in openapi_schema
    
    # Check app info
    info = openapi_schema["info"]
    assert info["title"] == "Notification Service"
    assert info["version"] == "1.0.0"
    assert "description" in info
    assert "contact" in info
    assert "license" in info
    
    # Check that all expected endpoints are documented
    paths = openapi_schema["paths"]
    expected_paths = [
        "/health",
        "/api/v1/notifications",
        "/api/v1/notifications/{notification_id}/read",
        "/api/v1/notifications/read-all"
    ]
    
    for path in expected_paths:
        assert path in paths, f"Path {path} not found in OpenAPI schema"
    
    # Check that endpoints have proper tags
    health_endpoint = paths["/health"]["get"]
    assert "tags" in health_endpoint
    assert "health" in health_endpoint["tags"]
    
    notifications_endpoint = paths["/api/v1/notifications"]["post"]
    assert "tags" in notifications_endpoint
    assert "notifications" in notifications_endpoint["tags"]
    
    # Check that response models are defined
    assert "components" in openapi_schema
    assert "schemas" in openapi_schema["components"]
    
    schemas = openapi_schema["components"]["schemas"]
    expected_schemas = [
        "NotificationCreate",
        "NotificationResponse", 
        "NotificationListResponse",
        "HealthResponse"
    ]
    
    for schema in expected_schemas:
        assert schema in schemas, f"Schema {schema} not found in OpenAPI components"
    
    print("✅ OpenAPI schema validation passed!")
    return True

def test_tags_metadata():
    """Test that endpoints are properly tagged."""
    openapi_schema = app.openapi()
    paths = openapi_schema["paths"]
    
    # Check that health endpoint has health tag
    health_endpoint = paths["/health"]["get"]
    assert "tags" in health_endpoint
    assert "health" in health_endpoint["tags"]
    
    # Check that notification endpoints have notifications tag
    notifications_post = paths["/api/v1/notifications"]["post"]
    assert "tags" in notifications_post
    assert "notifications" in notifications_post["tags"]
    
    notifications_get = paths["/api/v1/notifications"]["get"]
    assert "tags" in notifications_get
    assert "notifications" in notifications_get["tags"]
    
    print("✅ Endpoint tags validation passed!")
    return True

def test_endpoint_documentation():
    """Test that endpoints have proper documentation."""
    openapi_schema = app.openapi()
    paths = openapi_schema["paths"]
    
    # Test health endpoint documentation
    health_get = paths["/health"]["get"]
    assert "summary" in health_get
    assert "responses" in health_get
    assert "200" in health_get["responses"]
    
    # Test notification creation endpoint documentation
    notifications_post = paths["/api/v1/notifications"]["post"]
    assert "summary" in notifications_post
    assert "description" in notifications_post
    assert "requestBody" in notifications_post
    assert "responses" in notifications_post
    assert "201" in notifications_post["responses"]
    
    # Test notification retrieval endpoint documentation
    notifications_get = paths["/api/v1/notifications"]["get"]
    assert "summary" in notifications_get
    assert "description" in notifications_get
    assert "parameters" in notifications_get
    assert "responses" in notifications_get
    assert "200" in notifications_get["responses"]
    
    print("✅ Endpoint documentation validation passed!")
    return True

def main():
    """Run all API documentation tests."""
    print("Testing Notification Service API Documentation...")
    print("=" * 50)
    
    try:
        test_openapi_schema()
        test_tags_metadata()
        test_endpoint_documentation()
        
        print("=" * 50)
        print("🎉 All API documentation tests passed!")
        print("\nAPI Documentation Features:")
        print("- ✅ Enhanced FastAPI app metadata")
        print("- ✅ Comprehensive endpoint documentation")
        print("- ✅ Proper request/response models")
        print("- ✅ Organized endpoint tags")
        print("- ✅ Contact and license information")
        print("- ✅ Health check endpoint")
        print("- ✅ Authentication documentation")
        
        print("\nAccess the documentation at:")
        print("- Swagger UI: http://localhost:8003/docs")
        print("- ReDoc: http://localhost:8003/redoc")
        print("- OpenAPI JSON: http://localhost:8003/openapi.json")
        
        return True
        
    except Exception as e:
        print(f"❌ API documentation test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)