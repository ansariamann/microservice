"""
Task Service FastAPI application.
Provides REST API endpoints for task management.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase

# Add shared directory to path
sys.path.append('/app/shared')
from security_middleware import SecurityMiddleware, RequestLoggingMiddleware, RateLimiter, validate_request_data
from logging_config import setup_logging, get_logger, log_request, log_response, log_error
from health_check import HealthChecker, database_health_check, memory_usage_check, disk_usage_check, external_service_health_check
from metrics import metrics_collector, increment_counter, record_timing, get_metrics_summary, time_operation

from .database import db_manager, get_database
from .models import TaskCreate, TaskUpdate, TaskResponse
from .services import TaskService, get_task_service
from .auth import get_current_user
from .notification_client import close_notification_client


# Setup structured logging
setup_logging("task-service", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Initialize health checker
health_checker = HealthChecker("task-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    try:
        await db_manager.connect()
        
        # Register health checks
        health_checker.register_check("database", database_health_check(lambda: db_manager.is_connected()))
        health_checker.register_check("memory", memory_usage_check(threshold_percent=85.0))
        health_checker.register_check("disk", disk_usage_check(threshold_percent=90.0))
        
        # Check notification service connectivity
        async def check_notification_service():
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://notification-service:8003/health", timeout=5) as response:
                        return response.status == 200
            except:
                return False
        
        health_checker.register_check("notification_service", external_service_health_check("notification-service", check_notification_service))
        
        logger.info("Task Service started successfully")
        yield
    finally:
        # Shutdown
        await close_notification_client()
        await db_manager.disconnect()
        logger.info("Task Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Task Service",
    description="""
    Microservice for task management operations in a distributed system.
    
    ## Features
    
    * **Task CRUD Operations**: Create, read, update, and delete tasks
    * **Task Assignment**: Assign tasks to users and manage assignments
    * **Status Management**: Track task progress through different statuses
    * **Authorization**: JWT-based authentication and role-based access control
    * **Filtering**: Filter tasks by status, assignee, and creator
    
    ## Authentication
    
    All endpoints (except health check) require JWT authentication.
    Include the JWT token in the Authorization header:
    
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Task Statuses
    
    * `to_do`: Task is created but not started
    * `in_progress`: Task is being worked on
    * `done`: Task is completed
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Task Service API",
        "email": "support@taskservice.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Security middleware
rate_limiter = RateLimiter(max_requests=200, window_seconds=60)  # Higher limit for task operations
app.add_middleware(SecurityMiddleware, rate_limiter=rate_limiter)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware with stricter configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Total-Count"]
)


@app.get("/health")
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
                "service": "task-service",
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.get("/health/simple")
async def simple_health_check():
    """Simple health check endpoint for basic monitoring."""
    try:
        # Quick database check
        db_healthy = db_manager.is_connected()
        
        if db_healthy:
            return {
                "status": "healthy",
                "service": "task-service",
                "version": "1.0.0"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "service": "task-service",
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
                "service": "task-service",
                "version": "1.0.0",
                "error": str(e)
            }
        )


@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new task."""
    try:
        # Validate and sanitize input data
        validated_data = validate_request_data(task_data.dict())
        task_data = TaskCreate(**validated_data)
        
        task_service_instance = TaskService(database)
        created_task = await task_service_instance.create_task(task_data, current_user["user_id"])
        return created_task
        
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@app.get("/api/v1/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    status_filter: Optional[str] = Query(None, description="Filter tasks by status"),
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get tasks for the current user."""
    try:
        task_service = TaskService(database)
        
        if status_filter:
            tasks = await task_service.get_tasks_by_status(
                current_user["user_id"], status_filter, skip, limit
            )
        else:
            tasks = await task_service.get_user_tasks(current_user["user_id"], skip, limit)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific task by ID."""
    try:
        task_service = TaskService(database)
        task = await task_service.get_task_by_id(task_id, current_user["user_id"])
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return task
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task"
        )
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task"
        )


@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a task."""
    try:
        # Validate and sanitize input data
        validated_data = validate_request_data(task_update.dict(exclude_unset=True))
        task_update = TaskUpdate(**validated_data)
        
        task_service = TaskService(database)
        updated_task = await task_service.update_task(task_id, task_update, current_user["user_id"])
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return updated_task
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to update this task"
        )
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@app.delete("/api/v1/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a task."""
    try:
        task_service = TaskService(database)
        deleted = await task_service.delete_task(task_id, current_user["user_id"])
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return None
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to delete this task"
        )
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


@app.get("/api/v1/tasks/count")
async def get_task_count(
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get total task count for the current user."""
    try:
        task_service = TaskService(database)
        count = await task_service.count_user_tasks(current_user["user_id"])
        
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error counting tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count tasks"
        )


@app.put("/api/v1/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    assignee_data: dict,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Assign a task to a user."""
    try:
        assignee_id = assignee_data.get("assignee_id")
        if not assignee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assignee_id is required"
            )
        
        task_service = TaskService(database)
        updated_task = await task_service.assign_task(task_id, assignee_id, current_user["user_id"])
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return updated_task
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to assign this task"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign task"
        )


@app.put("/api/v1/tasks/{task_id}/unassign", response_model=TaskResponse)
async def unassign_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Remove assignment from a task."""
    try:
        task_service = TaskService(database)
        updated_task = await task_service.unassign_task(task_id, current_user["user_id"])
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return updated_task
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to unassign this task"
        )
    except Exception as e:
        logger.error(f"Error unassigning task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unassign task"
        )


@app.put("/api/v1/tasks/{task_id}/status", response_model=TaskResponse)
async def change_task_status(
    task_id: str,
    status_data: dict,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Change task status."""
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status is required"
            )
        
        # Validate status value
        from .models import TaskStatus
        try:
            status_enum = TaskStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TaskStatus]}"
            )
        
        task_service = TaskService(database)
        updated_task = await task_service.change_task_status(task_id, status_enum, current_user["user_id"])
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return updated_task
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied to change task status"
        )
    except Exception as e:
        logger.error(f"Error changing status for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change task status"
        )


@app.get("/api/v1/tasks/assigned", response_model=List[TaskResponse])
async def get_assigned_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get tasks assigned to the current user."""
    try:
        task_service = TaskService(database)
        tasks = await task_service.get_assigned_tasks(current_user["user_id"], skip, limit)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error retrieving assigned tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assigned tasks"
        )


@app.get("/api/v1/tasks/created", response_model=List[TaskResponse])
async def get_created_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get tasks created by the current user."""
    try:
        task_service = TaskService(database)
        tasks = await task_service.get_created_tasks(current_user["user_id"], skip, limit)
        
        return tasks
        
    except Exception as e:
        logger.error(f"Error retrieving created tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created tasks"
        )


@app.get("/metrics")
async def get_metrics():
    """Get performance metrics endpoint"""
    try:
        metrics_summary = get_metrics_summary()
        
        # Add service-specific metrics
        metrics_summary["service"] = "task-service"
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