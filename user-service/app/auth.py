"""
Authentication utilities for User Service
"""
import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional


class PasswordHasher:
    """Utility class for password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class JWTManager:
    """Utility class for JWT token management"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    def create_access_token(self, user_id: int, email: str) -> str:
        """Create a JWT access token for a user"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=self.expiration_hours)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": now,
            "exp": expire
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user_id(self, token: str) -> Optional[int]:
        """Extract user ID from JWT token"""
        payload = self.decode_token(token)
        if payload:
            return payload.get("user_id")
        return None


# Global instances
password_hasher = PasswordHasher()
jwt_manager = JWTManager()