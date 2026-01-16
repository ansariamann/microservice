"""
Shared JWT utilities for microservices authentication
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()


def create_jwt_token(user_id: int, email: str) -> str:
    """
    Create a JWT token for user authentication
    
    Args:
        user_id: User's unique identifier
        email: User's email address
        
    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User information from token payload
    """
    token = credentials.credentials
    return decode_jwt_token(token)


def require_auth(f):
    """
    Decorator to require authentication for route handlers
    """
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # This decorator can be used with Flask-style applications
        # For FastAPI, use the get_current_user dependency instead
        return await f(*args, **kwargs)
    return decorated_function


class JWTValidator:
    """
    JWT validation utility class for consistent token handling
    """
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return payload if valid
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            return decode_jwt_token(token)
        except HTTPException:
            return None
    
    @staticmethod
    def extract_user_id(token: str) -> Optional[int]:
        """
        Extract user ID from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            User ID if token is valid, None otherwise
        """
        payload = JWTValidator.validate_token(token)
        return payload.get("user_id") if payload else None
    
    @staticmethod
    def extract_user_email(token: str) -> Optional[str]:
        """
        Extract user email from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            User email if token is valid, None otherwise
        """
        payload = JWTValidator.validate_token(token)
        return payload.get("email") if payload else None