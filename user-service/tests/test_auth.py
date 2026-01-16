"""
Unit tests for authentication utilities
"""
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.auth import PasswordHasher, JWTManager


class TestPasswordHasher:
    """Test cases for PasswordHasher class"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = PasswordHasher.hash_password(password)
        
        # Hash should be different from original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should have reasonable length (bcrypt hashes are typically 60 chars)
        assert len(hashed) >= 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = PasswordHasher.hash_password(password)
        
        # Verification should succeed
        assert PasswordHasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = PasswordHasher.hash_password(password)
        
        # Verification should fail
        assert PasswordHasher.verify_password(wrong_password, hashed) is False

    def test_hash_same_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "test_password_123"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        
        # Hashes should be different due to different salts
        assert hash1 != hash2
        # But both should verify correctly
        assert PasswordHasher.verify_password(password, hash1) is True
        assert PasswordHasher.verify_password(password, hash2) is True


class TestJWTManager:
    """Test cases for JWTManager class"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        jwt_manager = JWTManager()
        user_id = 123
        email = "test@example.com"
        
        token = jwt_manager.create_access_token(user_id, email)
        
        # Token should be a string
        assert isinstance(token, str)
        # Token should have JWT structure (3 parts separated by dots)
        assert len(token.split('.')) == 3

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token"""
        jwt_manager = JWTManager()
        user_id = 123
        email = "test@example.com"
        
        token = jwt_manager.create_access_token(user_id, email)
        payload = jwt_manager.decode_token(token)
        
        # Payload should not be None
        assert payload is not None
        # Payload should contain expected data
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """Test decoding an invalid JWT token"""
        jwt_manager = JWTManager()
        invalid_token = "invalid.token.here"
        
        payload = jwt_manager.decode_token(invalid_token)
        
        # Payload should be None for invalid token
        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired JWT token"""
        jwt_manager = JWTManager()
        user_id = 123
        email = "test@example.com"
        
        # Create token with past expiration
        now = datetime.now(timezone.utc)
        past_time = now - timedelta(hours=1)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": past_time,
            "exp": past_time  # Already expired
        }
        
        expired_token = jwt.encode(payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        decoded_payload = jwt_manager.decode_token(expired_token)
        
        # Payload should be None for expired token
        assert decoded_payload is None

    def test_get_current_user_id_valid_token(self):
        """Test extracting user ID from valid token"""
        jwt_manager = JWTManager()
        user_id = 123
        email = "test@example.com"
        
        token = jwt_manager.create_access_token(user_id, email)
        extracted_user_id = jwt_manager.get_current_user_id(token)
        
        assert extracted_user_id == user_id

    def test_get_current_user_id_invalid_token(self):
        """Test extracting user ID from invalid token"""
        jwt_manager = JWTManager()
        invalid_token = "invalid.token.here"
        
        extracted_user_id = jwt_manager.get_current_user_id(invalid_token)
        
        assert extracted_user_id is None

    @patch.dict('os.environ', {
        'JWT_SECRET': 'test-secret',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_HOURS': '12'
    })
    def test_jwt_manager_with_env_vars(self):
        """Test JWTManager initialization with environment variables"""
        jwt_manager = JWTManager()
        
        assert jwt_manager.secret_key == 'test-secret'
        assert jwt_manager.algorithm == 'HS256'
        assert jwt_manager.expiration_hours == 12

    def test_jwt_manager_default_values(self):
        """Test JWTManager initialization with default values"""
        with patch.dict('os.environ', {}, clear=True):
            jwt_manager = JWTManager()
            
            assert jwt_manager.secret_key == 'your-secret-key-change-in-production'
            assert jwt_manager.algorithm == 'HS256'
            assert jwt_manager.expiration_hours == 24

    def test_token_expiration_time(self):
        """Test that token has correct expiration time"""
        jwt_manager = JWTManager()
        user_id = 123
        email = "test@example.com"
        
        before_creation = datetime.now(timezone.utc)
        token = jwt_manager.create_access_token(user_id, email)
        after_creation = datetime.now(timezone.utc)
        
        payload = jwt_manager.decode_token(token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        # Token should expire approximately 24 hours from creation (with some tolerance)
        expected_exp_min = before_creation + timedelta(hours=jwt_manager.expiration_hours) - timedelta(seconds=1)
        expected_exp_max = after_creation + timedelta(hours=jwt_manager.expiration_hours) + timedelta(seconds=1)
        
        assert expected_exp_min <= exp_datetime <= expected_exp_max