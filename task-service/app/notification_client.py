"""
Notification Client for Task Service

This module provides HTTP client functionality for communicating with the
Notification Service to create notifications for task-related events.
Includes retry logic, circuit breaker pattern, and graceful degradation.
"""

import asyncio
import logging
import os
import time
from enum import Enum
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class NotificationData(BaseModel):
    """Data model for notification creation requests."""
    user_id: int
    task_id: str
    message: str
    type: str


class CircuitBreaker:
    """Circuit breaker implementation for notification service calls."""
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises CircuitBreakerOpenException
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class NotificationClient:
    """HTTP client for communicating with the Notification Service with resilience features."""
    
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        timeout: float = 10.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout: float = 60.0
    ):
        """
        Initialize the notification client with resilience features.
        
        Args:
            base_url: Base URL of the notification service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
            max_delay: Maximum delay between retries (seconds)
            circuit_breaker_failure_threshold: Number of failures before opening circuit
            circuit_breaker_recovery_timeout: Time to wait before attempting recovery
        """
        self.base_url = base_url or os.getenv(
            "NOTIFICATION_SERVICE_URL", 
            "http://notification-service:8003"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        self.client = httpx.AsyncClient(timeout=timeout)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_failure_threshold,
            recovery_timeout=circuit_breaker_recovery_timeout,
            expected_exception=(httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError)
        )
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff."""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    async def _make_http_request(self, notification_data: NotificationData) -> bool:
        """Make HTTP request to notification service."""
        url = f"{self.base_url}/api/v1/notifications"
        
        response = await self.client.post(
            url,
            json=notification_data.model_dump(),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            return True
        else:
            # Treat non-201 responses as failures that should trigger retries
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code}", 
                request=response.request, 
                response=response
            )
    
    async def create_notification(self, notification_data: NotificationData) -> bool:
        """
        Create a notification via the Notification Service with retry logic and circuit breaker.
        
        Args:
            notification_data: Notification data to send
            
        Returns:
            True if notification was created successfully, False otherwise
        """
        logger.info(f"Creating notification for user {notification_data.user_id}")
        
        try:
            # Use circuit breaker to protect against cascading failures
            result = await self.circuit_breaker.call(
                self._create_notification_with_retry, 
                notification_data
            )
            logger.info(f"Successfully created notification for user {notification_data.user_id}")
            return result
            
        except CircuitBreakerOpenException:
            logger.warning(
                f"Circuit breaker is open, skipping notification for user {notification_data.user_id}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to create notification after all retries: {str(e)}")
            return False
    
    async def _create_notification_with_retry(self, notification_data: NotificationData) -> bool:
        """Create notification with retry logic and exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return await self._make_http_request(notification_data)
                
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = await self._calculate_delay(attempt)
                    logger.warning(
                        f"Notification attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} notification attempts failed. "
                        f"Last error: {str(e)}"
                    )
            except Exception as e:
                # For unexpected errors, don't retry
                logger.error(f"Unexpected error creating notification: {str(e)}")
                raise e
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        return False
    
    async def create_task_assigned_notification(
        self, 
        assignee_id: int, 
        task_id: str, 
        task_title: str, 
        assigner_name: str = "System"
    ) -> bool:
        """
        Create a notification for task assignment.
        
        Args:
            assignee_id: ID of the user being assigned the task
            task_id: ID of the task being assigned
            task_title: Title of the task
            assigner_name: Name of the user assigning the task
            
        Returns:
            True if notification was created successfully, False otherwise
        """
        message = f"You have been assigned to task '{task_title}' by {assigner_name}"
        
        notification_data = NotificationData(
            user_id=assignee_id,
            task_id=task_id,
            message=message,
            type="task_assigned"
        )
        
        return await self.create_notification(notification_data)
    
    async def create_task_status_notification(
        self, 
        user_id: int, 
        task_id: str, 
        task_title: str, 
        new_status: str,
        updater_name: str = "System"
    ) -> bool:
        """
        Create a notification for task status update.
        
        Args:
            user_id: ID of the user to notify
            task_id: ID of the task that was updated
            task_title: Title of the task
            new_status: New status of the task
            updater_name: Name of the user who updated the task
            
        Returns:
            True if notification was created successfully, False otherwise
        """
        # Format status for display
        status_display = new_status.replace("_", " ").title()
        message = f"Task '{task_title}' status has been updated to '{status_display}' by {updater_name}"
        
        notification_data = NotificationData(
            user_id=user_id,
            task_id=task_id,
            message=message,
            type="task_updated"
        )
        
        return await self.create_notification(notification_data)


# Global notification client instance
_notification_client: Optional[NotificationClient] = None


def get_notification_client() -> NotificationClient:
    """
    Get the global notification client instance.
    
    Returns:
        NotificationClient instance
    """
    global _notification_client
    if _notification_client is None:
        _notification_client = NotificationClient()
    return _notification_client


async def close_notification_client():
    """Close the global notification client."""
    global _notification_client
    if _notification_client is not None:
        await _notification_client.close()
        _notification_client = None