"""
Notification Service FastAPI Application

This module implements the notification service API endpoints for creating
and retrieving notifications in the task management system.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

# Import local modules
from .database import get_db_session, init_database, close_database
from .repository import NotificationRepository
from .models import Notification

# Import shared utilities
sys.path.append('/app/shared')
from jwt_utils import get_current_user
from security_middleware import SecurityMiddleware, RequestLoggingMiddleware, RateLimiter, validate_request_data
from logging_config import setup_logging, get_logger, log_request, log_response, log_error
from health_check import HealthChecker, database_health_check, memory_usage_check, disk_usage_check
from metrics import metrics_collector, increment_counter, record_timing, get_metrics_summary, time_operation

# Setup structured logging
setup_logging("notification-service", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize health checker
health_checker = HealthChecker("notification-service")


# Pydantic models for request/response
class NotificationCreate(BaseModel):
    """Request model for creating notifications."""
    user_id: int = Field(..., gt=0, description="ID of the user to notify")
    task_id: str = Field(..., min_length=1, description="ID of the related task")
    message: str = Field(..., min_length=1, max_length=500, description="Notification message")
    type: str = Field(..., description="Type of notification")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ['task_assigned', 'task_updated']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of: {allowed_types}')
        return v


class NotificationResponse(BaseModel):
    """Response model for notification data."""
    id: int
    user_id: int
    task_id: str
    message: str
    type: str
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    """Response model for notification list."""
    notifications: List[NotificationResponse]
    total: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str


# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("Starting Notification Service...")
    init_database()
    
    # Register health checks
    def check_database():
        try:
            # Test database connection by getting a session
            from sqlalchemy import text
            session = get_db_session()
            session.execute(text("SELECT 1"))
            session.close()
            return True
        except:
            return False
    
    health_checker.register_check("database", database_health_check(check_database))
    health_checker.register_check("memory", memory_usage_check(threshold_percent=85.0))
    health_checker.register_check("disk", disk_usage_check(threshold_percent=90.0))
    
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Service...")
    close_database()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Notification Service",
    description="""
    Microservice for managing task-related notifications in the task management system.
    
    This service provides endpoints for:
    - Creating notifications (internal service calls)
    - Retrieving user notifications (authenticated)
    - Marking notifications as read (authenticated)
    - Health monitoring
    
    ## Authentication
    
    Most endpoints require JWT authentication. Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Notification Types
    
    - `task_assigned`: When a task is assigned to a user
    - `task_updated`: When a task status is updated
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Task Management System",
        "url": "https://github.com/your-org/task-management",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring service status",
        },
        {
            "name": "notifications",
            "description": "Notification management operations",
        },
    ]
)

# Security middleware
rate_limiter = RateLimiter(max_requests=150, window_seconds=60)  # Moderate limit for notifications
app.add_middleware(SecurityMiddleware, rate_limiter=rate_limiter)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware with stricter configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"]
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_result = await health_checker.run_all_checks()
        
        # Determine HTTP status code based on overall health
        if health_result["status"] == "unhealthy":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            status_code = status.HTTP_200_OK
        
        # Add version info
        health_result["version"] = "1.0.0"
        
        if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise HTTPException(
                status_code=status_code,
                detail=health_result
            )
        
        return health_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "service": "notification-service",
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.get("/health/simple", tags=["health"])
async def simple_health_check():
    """Simple health check endpoint for basic monitoring."""
    try:
        # Quick database check
        from sqlalchemy import text
        session = get_db_session()
        session.execute(text("SELECT 1"))
        session.close()
        
        return {
            "status": "healthy",
            "service": "notification-service",
            "version": "1.0.0"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "notification-service",
                "version": "1.0.0",
                "error": str(e)
            }
        )


# Internal endpoint for creating notifications (no auth required)
@app.post("/api/v1/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED, tags=["notifications"])
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new notification (internal service endpoint).
    
    This endpoint is used by other services (like Task Service) to create
    notifications. It doesn't require authentication as it's for internal use.
    
    Args:
        notification_data: Notification creation data
        db: Database session
        
    Returns:
        Created notification data
    """
    try:
        # Validate and sanitize input data
        validated_data = validate_request_data(notification_data.dict())
        notification_data = NotificationCreate(**validated_data)
        
        logger.info(f"Creating notification for user {notification_data.user_id}")
        
        # Create notification instance
        notification = Notification(
            user_id=notification_data.user_id,
            task_id=notification_data.task_id,
            message=notification_data.message,
            type=notification_data.type
        )
        
        # Save to database
        repository = NotificationRepository(db)
        created_notification = repository.create_notification(notification)
        
        logger.info(f"Successfully created notification {created_notification.id}")
        
        return NotificationResponse(
            id=created_notification.id,
            user_id=created_notification.user_id,
            task_id=created_notification.task_id,
            message=created_notification.message,
            type=created_notification.type,
            is_read=created_notification.is_read,
            created_at=created_notification.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


# Authenticated endpoint for retrieving user notifications
@app.get("/api/v1/notifications", response_model=NotificationListResponse, tags=["notifications"])
async def get_user_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get notifications for the authenticated user.
    
    Args:
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications to return (default: 50)
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        List of user's notifications
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Retrieving notifications for user {user_id}")
        
        # Validate limit parameter
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        # Get notifications from database
        repository = NotificationRepository(db)
        notifications = repository.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
        
        # Convert to response format
        notification_responses = [
            NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                task_id=notification.task_id,
                message=notification.message,
                type=notification.type,
                is_read=notification.is_read,
                created_at=notification.created_at.isoformat()
            )
            for notification in notifications
        ]
        
        logger.info(f"Retrieved {len(notification_responses)} notifications for user {user_id}")
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=len(notification_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


# Authenticated endpoint for marking notifications as read
@app.put("/api/v1/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT, tags=["notifications"])
async def mark_notification_as_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Mark a specific notification as read.
    
    Args:
        notification_id: ID of the notification to mark as read
        current_user: Current authenticated user from JWT token
        db: Database session
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Marking notification {notification_id} as read for user {user_id}")
        
        repository = NotificationRepository(db)
        
        # First check if notification exists and belongs to user
        notification = repository.get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this notification"
            )
        
        # Mark as read
        success = repository.mark_notification_as_read(notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notification as read"
            )
        
        logger.info(f"Successfully marked notification {notification_id} as read")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


# Authenticated endpoint for marking all user notifications as read
@app.put("/api/v1/notifications/read-all", status_code=status.HTTP_200_OK, tags=["notifications"])
async def mark_all_notifications_as_read(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Mark all unread notifications for the authenticated user as read.
    
    Args:
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        Number of notifications marked as read
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Marking all notifications as read for user {user_id}")
        
        repository = NotificationRepository(db)
        count = repository.mark_user_notifications_as_read(user_id)
        
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        
        return {"marked_as_read": count}
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@app.get("/metrics", tags=["monitoring"])
async def get_metrics():
    """Get performance metrics endpoint"""
    try:
        metrics_summary = get_metrics_summary()
        
        # Add service-specific metrics
        metrics_summary["service"] = "notification-service"
        metrics_summary["version"] = "1.0.0"
        metrics_summary["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        return metrics_summary
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve metrics",
                "message": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)