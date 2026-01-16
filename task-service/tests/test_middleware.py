"""
Tests for Task Service middleware.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware import (
    AuthenticationMiddleware, RequestLoggingMiddleware, 
    ErrorHandlingMiddleware, setup_middleware
)
from app.auth import auth_settings


class TestAuthenticationMiddleware:
    """Test authentication middleware."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_endpoint(request: Request):
            user = getattr(request.state, 'user', None)
            return {"user": user}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def app_with_middleware(self, app):
        """Create app with authentication middleware."""
        app.add_middleware(AuthenticationMiddleware)
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)
    
    @pytest.fixture
    def valid_token(self):
        """Create valid JWT token."""
        payload = {
            "user_id": 1,
            "email": "test@example.com",
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now().timestamp())
        }
        return jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
    
    @pytest.fixture
    def expired_token(self):
        """Create expired JWT token."""
        payload = {
            "user_id": 1,
            "email": "test@example.com",
            "exp": int((datetime.now() - timedelta(hours=1)).timestamp()),
            "iat": int((datetime.now() - timedelta(hours=2)).timestamp())
        }
        return jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
    
    def test_excluded_path_no_auth(self, client):
        """Test that excluded paths don't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_protected_path_no_header(self, client):
        """Test protected path without authorization header."""
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_protected_path_invalid_format(self, client):
        """Test protected path with invalid authorization format."""
        response = client.get("/protected", headers={"Authorization": "InvalidFormat token"})
        assert response.status_code == 401
        assert "Invalid authorization format" in response.json()["detail"]
    
    def test_protected_path_invalid_token(self, client):
        """Test protected path with invalid token."""
        response = client.get("/protected", headers={"Authorization": "Bearer invalid.token"})
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_protected_path_expired_token(self, client, expired_token):
        """Test protected path with expired token."""
        response = client.get("/protected", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_protected_path_valid_token(self, client, valid_token):
        """Test protected path with valid token."""
        response = client.get("/protected", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["user"]["user_id"] == 1
        assert data["user"]["email"] == "test@example.com"
    
    def test_custom_exclude_paths(self):
        """Test middleware with custom exclude paths."""
        app = FastAPI()
        
        @app.get("/custom-health")
        async def custom_health():
            return {"status": "ok"}
        
        app.add_middleware(AuthenticationMiddleware, exclude_paths=["/custom-health"])
        client = TestClient(app)
        
        response = client.get("/custom-health")
        assert response.status_code == 200


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def app_with_middleware(self, app):
        """Create app with logging middleware."""
        app.add_middleware(RequestLoggingMiddleware)
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)
    
    @patch('app.middleware.logger')
    def test_request_logging(self, mock_logger, client):
        """Test that requests are logged."""
        response = client.get("/test")
        assert response.status_code == 200
        
        # Verify logging calls
        mock_logger.info.assert_any_call("Request: GET /test")
        mock_logger.info.assert_any_call("Response: 200 for GET /test")


class TestErrorHandlingMiddleware:
    """Test error handling middleware."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/permission-error")
        async def permission_error_endpoint():
            raise PermissionError("Access denied")
        
        @app.get("/value-error")
        async def value_error_endpoint():
            raise ValueError("Invalid input")
        
        @app.get("/generic-error")
        async def generic_error_endpoint():
            raise Exception("Something went wrong")
        
        @app.get("/http-error")
        async def http_error_endpoint():
            raise HTTPException(status_code=404, detail="Not found")
        
        return app
    
    @pytest.fixture
    def app_with_middleware(self, app):
        """Create app with error handling middleware."""
        app.add_middleware(ErrorHandlingMiddleware)
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)
    
    def test_permission_error_handling(self, client):
        """Test PermissionError handling."""
        response = client.get("/permission-error")
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied"
    
    def test_value_error_handling(self, client):
        """Test ValueError handling."""
        response = client.get("/value-error")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid input"
    
    def test_generic_error_handling(self, client):
        """Test generic Exception handling."""
        response = client.get("/generic-error")
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error"
    
    def test_http_exception_passthrough(self, client):
        """Test that HTTPExceptions are passed through."""
        response = client.get("/http-error")
        assert response.status_code == 404
        assert response.json()["detail"] == "Not found"


class TestSetupMiddleware:
    """Test middleware setup function."""
    
    def test_setup_middleware(self):
        """Test that setup_middleware adds all middleware."""
        app = FastAPI()
        
        # Mock the add_middleware method to track calls
        app.add_middleware = MagicMock()
        
        setup_middleware(app)
        
        # Verify all middleware were added
        assert app.add_middleware.call_count == 3
        
        # Check that middleware classes were added
        calls = app.add_middleware.call_args_list
        middleware_classes = [call[0][0] for call in calls]
        
        assert ErrorHandlingMiddleware in middleware_classes
        assert RequestLoggingMiddleware in middleware_classes
        assert AuthenticationMiddleware in middleware_classes