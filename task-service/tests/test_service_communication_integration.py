"""
Integration tests for service communication failure scenarios.
Tests the Task Service behavior when the Notification Service is unavailable.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from datetime import datetime, timedelta

from app.services import TaskService
from app.models import TaskCreate, TaskUpdate, TaskStatus, TaskInDB
from app.notification_client import NotificationClient, CircuitBreakerState


class TestServiceCommunicationFailures:
    """Integration tests for service communication failure scenarios."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock task repository."""
        return AsyncMock()
    
    @pytest.fixture
    def task_service(self, mock_repository):
        """Create a task service with mock repository."""
        service = TaskService.__new__(TaskService)
        service.repository = mock_repository
        return service
    
    @pytest.fixture
    def sample_task_in_db(self):
        """Sample task from database."""
        from bson import ObjectId
        return TaskInDB(
            id=ObjectId(),
            title="Integration Test Task",
            description="Test task for integration testing",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_task_assignment_with_notification_service_down(self, task_service, mock_repository, sample_task_in_db):
        """Test task assignment when notification service is completely down."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.model_copy()
        updated_task.assignee_id = 2
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client to simulate service down
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_assigned_notification.side_effect = httpx.ConnectError("Service unavailable")
            mock_get_client.return_value = mock_client
            
            # Execute - task assignment should succeed despite notification failure
            result = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=2, user_id=1)
            
            # Verify task assignment succeeded
            assert result is not None
            assert result.assignee_id == 2
            
            # Verify notification was attempted
            mock_client.create_task_assigned_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_status_update_with_notification_timeout(self, task_service, mock_repository, sample_task_in_db):
        """Test task status update when notification service times out."""
        # Setup mocks - task starts with TO_DO status
        task_with_assignee = sample_task_in_db.model_copy()
        task_with_assignee.assignee_id = 2  # Add assignee so notification will be sent
        mock_repository.get_task_by_id.return_value = task_with_assignee
        
        updated_task = task_with_assignee.model_copy()
        updated_task.status = TaskStatus.IN_PROGRESS
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client to simulate timeout
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_status_notification.side_effect = httpx.TimeoutException("Request timeout")
            mock_get_client.return_value = mock_client
            
            # Execute - status update should succeed despite notification timeout
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=1)
            
            # Verify status update succeeded
            assert result is not None
            assert result.status == TaskStatus.IN_PROGRESS
            
            # Verify notification was attempted (to assignee since creator is updating)
            mock_client.create_task_status_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_task_operations_with_circuit_breaker(self, task_service, mock_repository, sample_task_in_db):
        """Test multiple task operations with circuit breaker protection."""
        # Setup mocks - return the same task for get_task_by_id
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Setup different updated tasks for each assignment
        updated_task1 = sample_task_in_db.model_copy()
        updated_task1.assignee_id = 2
        
        updated_task2 = sample_task_in_db.model_copy()
        updated_task2.assignee_id = 3
        
        updated_task3 = sample_task_in_db.model_copy()
        updated_task3.assignee_id = 4
        
        mock_repository.update_task.side_effect = [updated_task1, updated_task2, updated_task3]
        
        # Create a real notification client with circuit breaker for testing
        notification_client = NotificationClient(
            base_url="http://unavailable-service:8003",
            max_retries=1,
            base_delay=0.1,
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=5.0
        )
        
        with patch('app.services.get_notification_client', return_value=notification_client):
            with patch.object(notification_client.client, 'post') as mock_post:
                # All HTTP calls fail
                mock_post.side_effect = httpx.ConnectError("Service unavailable")
                
                # First task assignment - should trigger retries
                result1 = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=2, user_id=1)
                assert result1 is not None
                assert result1.assignee_id == 2
                
                # Second task assignment - should trigger retries and open circuit breaker
                result2 = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=3, user_id=1)
                assert result2 is not None
                assert result2.assignee_id == 3
                
                # Circuit breaker should now be open
                assert notification_client.circuit_breaker.state == CircuitBreakerState.OPEN
                
                # Third task assignment - should be blocked by circuit breaker (no HTTP calls)
                result3 = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=4, user_id=1)
                assert result3 is not None
                assert result3.assignee_id == 4
                
                # Should have made 4 HTTP calls total (2 operations * 2 attempts each)
                assert mock_post.call_count == 4
        
        await notification_client.close()
    
    @pytest.mark.asyncio
    async def test_notification_service_recovery_after_circuit_breaker_timeout(self, task_service, mock_repository, sample_task_in_db):
        """Test notification service recovery after circuit breaker timeout."""
        # Setup mocks - return the same task for get_task_by_id
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Setup different updated tasks for each assignment
        updated_task1 = sample_task_in_db.model_copy()
        updated_task1.assignee_id = 2
        
        updated_task2 = sample_task_in_db.model_copy()
        updated_task2.assignee_id = 3
        
        updated_task3 = sample_task_in_db.model_copy()
        updated_task3.assignee_id = 4
        
        mock_repository.update_task.side_effect = [updated_task1, updated_task2, updated_task3]
        
        # Create notification client with short recovery timeout
        notification_client = NotificationClient(
            base_url="http://test-service:8003",
            max_retries=1,
            base_delay=0.1,
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=1.0  # Short timeout for testing
        )
        
        with patch('app.services.get_notification_client', return_value=notification_client):
            with patch.object(notification_client.client, 'post') as mock_post:
                # First, open the circuit breaker with failures
                mock_post.side_effect = httpx.ConnectError("Service unavailable")
                
                # Two failed operations to open circuit breaker
                await task_service.assign_task(str(sample_task_in_db.id), assignee_id=2, user_id=1)
                await task_service.assign_task(str(sample_task_in_db.id), assignee_id=3, user_id=1)
                
                assert notification_client.circuit_breaker.state == CircuitBreakerState.OPEN
                
                # Simulate time passage for circuit breaker recovery
                import time
                notification_client.circuit_breaker.last_failure_time = time.time() - 2.0
                
                # Now make service available again
                mock_success_response = MagicMock()
                mock_success_response.status_code = 201
                mock_post.side_effect = None
                mock_post.return_value = mock_success_response
                
                # Next operation should succeed and reset circuit breaker
                result = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=4, user_id=1)
                assert result is not None
                assert result.assignee_id == 4
                
                # Circuit breaker should be closed again
                assert notification_client.circuit_breaker.state == CircuitBreakerState.CLOSED
        
        await notification_client.close()
    
    @pytest.mark.asyncio
    async def test_partial_notification_failures_dont_affect_task_operations(self, task_service, mock_repository, sample_task_in_db):
        """Test that partial notification failures don't affect task operations."""
        # Setup mocks for multiple tasks
        task1 = sample_task_in_db.model_copy()
        task1.assignee_id = None
        
        task2 = sample_task_in_db.model_copy()
        task2.assignee_id = None
        
        mock_repository.get_task_by_id.side_effect = [task1, task2]
        
        updated_task1 = task1.model_copy()
        updated_task1.assignee_id = 2
        
        updated_task2 = task2.model_copy()
        updated_task2.assignee_id = 3
        
        mock_repository.update_task.side_effect = [updated_task1, updated_task2]
        
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            # First notification fails, second succeeds
            mock_client.create_task_assigned_notification.side_effect = [
                httpx.TimeoutException("Timeout"),
                True
            ]
            mock_get_client.return_value = mock_client
            
            # Execute both task assignments
            result1 = await task_service.assign_task(str(task1.id), assignee_id=2, user_id=1)
            result2 = await task_service.assign_task(str(task2.id), assignee_id=3, user_id=1)
            
            # Both task assignments should succeed
            assert result1 is not None
            assert result1.assignee_id == 2
            assert result2 is not None
            assert result2.assignee_id == 3
            
            # Both notifications should have been attempted
            assert mock_client.create_task_assigned_notification.call_count == 2
    
    @pytest.mark.asyncio
    async def test_notification_service_http_errors_are_handled_gracefully(self, task_service, mock_repository, sample_task_in_db):
        """Test that HTTP errors from notification service are handled gracefully."""
        # Setup mocks - task starts with TO_DO status and has assignee for notifications
        task_with_assignee = sample_task_in_db.model_copy()
        task_with_assignee.assignee_id = 2
        mock_repository.get_task_by_id.return_value = task_with_assignee
        
        # Setup different updated tasks for each status change
        updated_task1 = task_with_assignee.model_copy()
        updated_task1.status = TaskStatus.IN_PROGRESS
        
        updated_task2 = task_with_assignee.model_copy()
        updated_task2.status = TaskStatus.DONE
        
        updated_task3 = task_with_assignee.model_copy()
        updated_task3.status = TaskStatus.TO_DO
        
        mock_repository.update_task.side_effect = [updated_task1, updated_task2, updated_task3]
        
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            # Simulate various HTTP errors
            mock_client.create_task_status_notification.side_effect = [
                httpx.HTTPStatusError("HTTP 500", request=MagicMock(), response=MagicMock()),
                httpx.HTTPStatusError("HTTP 503", request=MagicMock(), response=MagicMock()),
                httpx.HTTPStatusError("HTTP 404", request=MagicMock(), response=MagicMock())
            ]
            mock_get_client.return_value = mock_client
            
            # Execute multiple status updates
            expected_statuses = [TaskStatus.IN_PROGRESS, TaskStatus.DONE]
            for i, new_status in enumerate(expected_statuses):
                result = await task_service.change_task_status(str(sample_task_in_db.id), new_status, user_id=1)
                
                # Task operations should succeed despite notification failures
                assert result is not None
                assert result.status == expected_statuses[i]
            
            # Execute one more status update by the assignee (user 2) to test third HTTP error
            updated_task3 = task_with_assignee.model_copy()
            updated_task3.status = TaskStatus.IN_PROGRESS
            mock_repository.update_task.side_effect = [updated_task3]  # Reset side_effect for next call
            
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=2)
            assert result is not None
            assert result.status == TaskStatus.IN_PROGRESS
            
            # All three notifications should have been attempted
            assert mock_client.create_task_status_notification.call_count == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_task_operations_with_notification_failures(self, task_service, mock_repository, sample_task_in_db):
        """Test concurrent task operations with notification service failures."""
        import asyncio
        
        # Setup mocks for concurrent operations
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.model_copy()
        updated_task.assignee_id = 2
        mock_repository.update_task.return_value = updated_task
        
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            # Some notifications fail, some succeed
            mock_client.create_task_assigned_notification.side_effect = [
                True,  # Success
                httpx.TimeoutException("Timeout"),  # Failure
                True,  # Success
                httpx.ConnectError("Connection failed"),  # Failure
                True   # Success
            ]
            mock_get_client.return_value = mock_client
            
            # Execute concurrent task assignments
            tasks = []
            for i in range(5):
                task = task_service.assign_task(str(sample_task_in_db.id), assignee_id=i+2, user_id=1)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All task assignments should succeed
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None
                assert result.assignee_id >= 2
            
            # All notifications should have been attempted
            assert mock_client.create_task_assigned_notification.call_count == 5