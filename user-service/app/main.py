"""
FastAPI application for User Service
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os
import sys
import logging

# Add shared directory to path
sys.path.append('/app/shared')
from security_middleware import SecurityMiddleware, RequestLoggingMiddleware, RateLimiter, validate_request_data
from logging_config import setup_logging, get_logger, log_request, log_response, log_error
from health_check import HealthChecker, database_health_check, memory_usage_check, disk_usage_check
from metrics import metrics_collector, increment_counter, record_timing, get_metrics_summary, time_operation

from .database import get_db, init_db, check_db_connection
from .schemas import UserRegistration, UserLogin, TokenResponse, ErrorResponse, UserResponse, UserProfileUpdate
from .services import UserService
from .middleware import get_current_user
from .models import User

# Setup structured logging
setup_logging("user-service", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize health checker
health_checker = HealthChecker("user-service")

# Initialize FastAPI app
app = FastAPI(
    title="User Service",
    description="Microservice for user registration, authentication, and profile management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Task Management System",
        "email": "admin@taskmanagement.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Security middleware
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
app.add_middleware(SecurityMiddleware, rate_limiter=rate_limiter)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware with stricter configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"]
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Register health checks
    health_checker.register_check("database", database_health_check(check_db_connection))
    health_checker.register_check("memory", memory_usage_check(threshold_percent=85.0))
    health_checker.register_check("disk", disk_usage_check(threshold_percent=90.0))
    
    logger.info("User Service started successfully")


@app.post(
    "/api/v1/register", 
    response_model=TokenResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, and name. Returns JWT token for immediate authentication.",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Registration error (e.g., email already exists)"},
        500: {"description": "Internal server error"}
    }
)
async def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    with time_operation("user.register", {"endpoint": "/api/v1/register"}):
        try:
            # Validate and sanitize input data
            validated_data = validate_request_data(user_data.dict())
            user_data = UserRegistration(**validated_data)
            
            user_service = UserService(db)
            token_response = user_service.register_user(user_data)
            
            # Record success metrics
            increment_counter("user.register.success", 1.0, {"endpoint": "/api/v1/register"})
            
            return token_response
        except ValueError as e:
            increment_counter("user.register.error", 1.0, {"endpoint": "/api/v1/register", "error_type": "validation"})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.create(
                    code="REGISTRATION_ERROR",
                    message=str(e)
                ).dict()
            )
        except Exception as e:
            increment_counter("user.register.error", 1.0, {"endpoint": "/api/v1/register", "error_type": "internal"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.create(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred"
                ).dict()
            )


@app.post(
    "/api/v1/login", 
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate a user with email and password. Returns JWT token for accessing protected endpoints.",
    responses={
        200: {"description": "User successfully authenticated"},
        401: {"description": "Invalid credentials"},
        500: {"description": "Internal server error"}
    }
)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate a user and return JWT token"""
    with time_operation("user.login", {"endpoint": "/api/v1/login"}):
        try:
            # Validate and sanitize input data
            validated_data = validate_request_data(login_data.dict())
            login_data = UserLogin(**validated_data)
            
            user_service = UserService(db)
            token_response = user_service.authenticate_user(login_data)
            
            # Record success metrics
            increment_counter("user.login.success", 1.0, {"endpoint": "/api/v1/login"})
            
            return token_response
        except ValueError as e:
            increment_counter("user.login.error", 1.0, {"endpoint": "/api/v1/login", "error_type": "authentication"})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse.create(
                    code="AUTHENTICATION_ERROR",
                    message=str(e)
                ).dict()
            )
        except Exception as e:
            increment_counter("user.login.error", 1.0, {"endpoint": "/api/v1/login", "error_type": "internal"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.create(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred"
                ).dict()
            )


@app.get(
    "/api/v1/profile", 
    response_model=UserResponse,
    summary="Get user profile",
    description="Retrieve the current authenticated user's profile information.",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    with time_operation("user.profile.get", {"endpoint": "/api/v1/profile"}):
        try:
            user_service = UserService(db)
            user_profile = user_service.get_user_profile(current_user)
            
            # Record success metrics
            increment_counter("user.profile.get.success", 1.0, {"endpoint": "/api/v1/profile"})
            
            return user_profile
        except Exception as e:
            increment_counter("user.profile.get.error", 1.0, {"endpoint": "/api/v1/profile", "error_type": "internal"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.create(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred"
                ).dict()
            )


@app.put(
    "/api/v1/profile", 
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the current authenticated user's profile information (name and/or email).",
    responses={
        200: {"description": "User profile updated successfully"},
        400: {"description": "Update error (e.g., email already exists)"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def update_user_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    with time_operation("user.profile.update", {"endpoint": "/api/v1/profile"}):
        try:
            # Validate and sanitize input data
            validated_data = validate_request_data(update_data.dict())
            update_data = UserProfileUpdate(**validated_data)
            
            user_service = UserService(db)
            updated_profile = user_service.update_user_profile(current_user, update_data)
            
            # Record success metrics
            increment_counter("user.profile.update.success", 1.0, {"endpoint": "/api/v1/profile"})
            
            return updated_profile
        except ValueError as e:
            increment_counter("user.profile.update.error", 1.0, {"endpoint": "/api/v1/profile", "error_type": "validation"})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.create(
                    code="PROFILE_UPDATE_ERROR",
                    message=str(e)
                ).dict()
            )
        except Exception as e:
            increment_counter("user.profile.update.error", 1.0, {"endpoint": "/api/v1/profile", "error_type": "internal"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.create(
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred"
                ).dict()
            )


@app.get(
    "/health",
    summary="Comprehensive health check",
    description="Check the health status of the User Service including database, system metrics, and performance.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check():
    """Comprehensive health check endpoint"""
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
                "service": "user-service",
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.get(
    "/health/simple",
    summary="Simple health check",
    description="Simple health check for basic monitoring.",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def simple_health_check():
    """Simple health check endpoint for basic monitoring"""
    try:
        # Quick database check
        db_healthy = check_db_connection()
        
        if db_healthy:
            return {
                "status": "healthy",
                "service": "user-service",
                "version": "1.0.0"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "service": "user-service",
                    "version": "1.0.0",
                    "error": "Database connection failed"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "user-service",
                "version": "1.0.0",
                "error": str(e)
            }
        )


@app.get(
    "/metrics",
    summary="Performance metrics",
    description="Get performance metrics and statistics for the User Service.",
    responses={
        200: {"description": "Metrics retrieved successfully"}
    }
)
async def get_metrics():
    """Get performance metrics endpoint"""
    try:
        metrics_summary = get_metrics_summary()
        
        # Add service-specific metrics
        metrics_summary["service"] = "user-service"
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
    port = int(os.getenv("SERVICE_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)