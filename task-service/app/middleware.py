"""
Middleware for Task Service.
Handles authentication, authorization, and request processing.
"""

import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import decode_jwt_token


logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token authentication."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication."""
        path = request.url.path
        
        # Skip authentication for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Extract authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            logger.warning(f"Missing authorization header for {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate Bearer token format
        if not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization format for {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract and validate token
        token = authorization.split(" ")[1]
        payload = decode_jwt_token(token)
        
        if not payload:
            logger.warning(f"Invalid or expired token for {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user info to request state
        request.state.user = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email")
        }
        
        logger.info(f"Authenticated user {payload.get('user_id')} for {path}")
        
        # Continue with request
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and exceptions."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except PermissionError as e:
            logger.warning(f"Permission denied for {request.url.path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
            
        except ValueError as e:
            logger.warning(f"Validation error for {request.url.path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        except Exception as e:
            logger.error(f"Unexpected error for {request.url.path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


def setup_middleware(app):
    """Setup all middleware for the application."""
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)