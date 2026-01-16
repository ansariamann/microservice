"""
Unit tests for middleware
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.middleware import get_current_user, get_current_user_optional
from app.models import User
from app.auth import jwt_manager


class TestMiddleware:
    """Test cases for authentication middleware"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session):
        """Test get_current_user with valid token"""
        # Create a user
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create valid token
        token = jwt_manager.create_access_token(user.id, user.email)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Test middleware
        result_user = await get_current_user(credentials, db_session)
        
        assert result_user.id == user.id
        assert result_user.email == user.email
        assert result_user.name == user.name

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test get_current_user with invalid token"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "INVALID_TOKEN" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session):
        """Test get_current_user with expired token"""
        # Create expired token manually
        import jwt
        from datetime import datetime, timezone, timedelta
        
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {
            "user_id": 123,
            "email": "test@example.com",
            "iat": past_time,
            "exp": past_time  # Already expired
        }
        
        expired_token = jwt.encode(payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "INVALID_TOKEN" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session):
        """Test get_current_user when user doesn't exist in database"""
        # Create token for non-existent user
        token = jwt_manager.create_access_token(999, "nonexistent@example.com")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "USER_NOT_FOUND" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_token_missing_user_id(self, db_session):
        """Test get_current_user with token missing user_id"""
        import jwt
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        payload = {
            "email": "test@example.com",
            "iat": now,
            "exp": now + timedelta(hours=1)
            # Missing user_id
        }
        
        invalid_token = jwt.encode(payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "INVALID_TOKEN" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_current_user_optional_valid_token(self, db_session):
        """Test get_current_user_optional with valid token"""
        # Create a user
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create valid token
        token = jwt_manager.create_access_token(user.id, user.email)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Test middleware
        result_user = await get_current_user_optional(credentials, db_session)
        
        assert result_user is not None
        assert result_user.id == user.id
        assert result_user.email == user.email

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self, db_session):
        """Test get_current_user_optional with no credentials"""
        result_user = await get_current_user_optional(None, db_session)
        assert result_user is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_invalid_token(self, db_session):
        """Test get_current_user_optional with invalid token"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
        
        result_user = await get_current_user_optional(credentials, db_session)
        assert result_user is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_user_not_found(self, db_session):
        """Test get_current_user_optional when user doesn't exist"""
        # Create token for non-existent user
        token = jwt_manager.create_access_token(999, "nonexistent@example.com")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        result_user = await get_current_user_optional(credentials, db_session)
        assert result_user is None