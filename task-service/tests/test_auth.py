"""
Tests for authentication and authorization utilities.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import decode_jwt_token, get_current_user, verify_token, auth_settings


class TestAuthUtilities:
    """Test authentication utilities."""
    
    @pytest.fixture
    def valid_payload(self):
        """Valid JWT payload."""
        now = datetime.now()
        return {
            "user_id": 1,
            "email": "test@example.com",
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iat": int(now.timestamp())
        }
    
    @pytest.fixture
    def expired_payload(self):
        """Expired JWT payload."""
        now = datetime.now()
        return {
            "user_id": 1,
            "email": "test@example.com",
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "iat": int((now - timedelta(hours=2)).timestamp())
        }
    
    def test_decode_jwt_token_valid(self, valid_payload):
        """Test decoding valid JWT token."""
        # Create token
        token = jwt.encode(valid_payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        
        # Decode token
        result = decode_jwt_token(token)
        
        # Verify
        assert result is not None
        assert result["user_id"] == 1
        assert result["email"] == "test@example.com"
    
    def test_decode_jwt_token_expired(self, expired_payload):
        """Test decoding expired JWT token."""
        # Create expired token
        token = jwt.encode(expired_payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        
        # Decode token
        result = decode_jwt_token(token)
        
        # Verify
        assert result is None
    
    def test_decode_jwt_token_invalid_signature(self, valid_payload):
        """Test decoding token with invalid signature."""
        # Create token with wrong secret
        token = jwt.encode(valid_payload, "wrong-secret", algorithm=auth_settings.jwt_algorithm)
        
        # Decode token
        result = decode_jwt_token(token)
        
        # Verify
        assert result is None
    
    def test_decode_jwt_token_malformed(self):
        """Test decoding malformed token."""
        # Use malformed token
        token = "invalid.token.format"
        
        # Decode token
        result = decode_jwt_token(token)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, valid_payload):
        """Test getting current user with valid token."""
        # Create token
        token = jwt.encode(valid_payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Get current user
        result = await get_current_user(credentials)
        
        # Verify
        assert result["user_id"] == 1
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(self):
        """Test getting current user with token missing user_id."""
        # Create token without user_id
        payload = {
            "email": "test@example.com",
            "exp": datetime.now() + timedelta(hours=1)
        }
        token = jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_email(self):
        """Test getting current user with token missing email."""
        # Create token without email
        payload = {
            "user_id": 1,
            "exp": datetime.now() + timedelta(hours=1)
        }
        token = jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Verify exception is raised
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail
    
    def test_verify_token_valid(self, valid_payload):
        """Test verifying valid token."""
        # Create token
        token = jwt.encode(valid_payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        
        # Verify token
        result = verify_token(token)
        
        # Verify
        assert result is True
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        # Use invalid token
        token = "invalid.token"
        
        # Verify token
        result = verify_token(token)
        
        # Verify
        assert result is False
    
    def test_verify_token_expired(self, expired_payload):
        """Test verifying expired token."""
        # Create expired token
        token = jwt.encode(expired_payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
        
        # Verify token
        result = verify_token(token)
        
        # Verify
        assert result is False


class TestAuthSettings:
    """Test authentication settings."""
    
    def test_default_settings(self):
        """Test default authentication settings."""
        settings = auth_settings
        
        assert settings.jwt_secret == "your-secret-key-change-in-production"
        assert settings.jwt_algorithm == "HS256"
    
    @patch.dict('os.environ', {'JWT_SECRET': 'test-secret', 'JWT_ALGORITHM': 'HS512'})
    def test_environment_settings(self):
        """Test authentication settings from environment."""
        from app.auth import AuthSettings
        settings = AuthSettings()
        
        assert settings.jwt_secret == "test-secret"
        assert settings.jwt_algorithm == "HS512"