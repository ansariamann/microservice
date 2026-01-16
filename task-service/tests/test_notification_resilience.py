"""
Tests for notification client resilience features including circuit breaker,
retry logic with exponential backoff, and graceful degradation.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.notification_client import (
    NotificationClient,
    NotificationData,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenException
)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker implementation."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=Exception
        )
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_initial_state(self, circuit_breaker):
        """Test circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_call(self, circuit_breaker):
        """Test successful call through circuit breaker."""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_count(self, circuit_breaker):
        """Test circuit breaker counts failures."""
        async def failing_func():
            raise Exception("Test failure")
        
        # First two failures should not open circuit
        for i in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
            assert circuit_breaker.state == CircuitBreakerState.CLOSED
            assert circuit_breaker.failure_count == i + 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self, circuit_breaker):
        """Test circuit breaker opens after failure threshold."""
        async def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures to reach threshold
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.failure_count == 3
        assert circuit_breaker.last_failure_time is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_calls_when_open(self, circuit_breaker):
        """Test circuit breaker blocks calls when open."""
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Now calls should be blocked
        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self, circuit_breaker):
        """Test circuit breaker transitions to HALF_OPEN after timeout."""
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Manually set time to simulate timeout
        circuit_breaker.last_failure_time = time.time() - 10.0  # 10 seconds ago
        
        # Next call should transition to HALF_OPEN and succeed
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success_in_half_open(self, circuit_breaker):
        """Test circuit breaker resets to CLOSED on success in HALF_OPEN state."""
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Force transition to HALF_OPEN
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        circuit_breaker.last_failure_time = time.time() - 10.0
        
        # Successful call should reset to CLOSED
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0


class TestNotificationClientResilience:
    """Test cases for NotificationClient resilience features."""
    
    @pytest.fixture
    def resilient_client(self):
        """Create a notification client with resilience features."""
        return NotificationClient(
            base_url="http://test-service:8003",
            timeout=5.0,
            max_retries=2,
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=5.0
        )
    
    @pytest.fixture
    def notification_data(self):
        """Create test notification data."""
        return NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification",
            type="task_assigned"
        )
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, resilient_client):
        """Test exponential backoff delay calculation."""
        # Test delay calculation
        delay_0 = await resilient_client._calculate_delay(0)
        delay_1 = await resilient_client._calculate_delay(1)
        delay_2 = await resilient_client._calculate_delay(2)
        
        assert delay_0 == 0.1  # base_delay * 2^0
        assert delay_1 == 0.2  # base_delay * 2^1
        assert delay_2 == 0.4  # base_delay * 2^2
        
        # Test max delay cap
        delay_large = await resilient_client._calculate_delay(10)
        assert delay_large == 1.0  # Should be capped at max_delay
    
    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self, resilient_client, notification_data):
        """Test successful request without retries."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is True
            assert mock_post.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, resilient_client, notification_data):
        """Test retry logic on timeout exceptions."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # First two calls timeout, third succeeds
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.side_effect = [
                httpx.TimeoutException("Timeout 1"),
                httpx.TimeoutException("Timeout 2"),
                mock_response
            ]
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is True
            assert mock_post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, resilient_client, notification_data):
        """Test retry logic on connection errors."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # First call fails, second succeeds
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.side_effect = [
                httpx.ConnectError("Connection failed"),
                mock_response
            ]
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is True
            assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_on_http_error(self, resilient_client, notification_data):
        """Test retry logic on HTTP errors."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # First call returns 500, second succeeds
            mock_error_response = MagicMock()
            mock_error_response.status_code = 500
            mock_error_response.request = MagicMock()
            
            mock_success_response = MagicMock()
            mock_success_response.status_code = 201
            
            mock_post.side_effect = [mock_error_response, mock_success_response]
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is True
            assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, resilient_client, notification_data):
        """Test behavior when all retries are exhausted."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # All calls timeout
            mock_post.side_effect = httpx.TimeoutException("Persistent timeout")
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is False
            assert mock_post.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, resilient_client, notification_data):
        """Test circuit breaker integration with notification client."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # All calls fail to trigger circuit breaker
            mock_post.side_effect = httpx.TimeoutException("Persistent failure")
            
            # Make enough failed calls to open circuit breaker
            for i in range(3):
                result = await resilient_client.create_notification(notification_data)
                assert result is False
            
            # Circuit breaker should now be open
            assert resilient_client.circuit_breaker.state == CircuitBreakerState.OPEN
            
            # Next call should be blocked by circuit breaker
            result = await resilient_client.create_notification(notification_data)
            assert result is False
            
            # Should not have made additional HTTP calls due to circuit breaker
            assert mock_post.call_count == 9  # 3 calls * 3 attempts each
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, resilient_client, notification_data):
        """Test circuit breaker recovery after timeout."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # First, open the circuit breaker
            mock_post.side_effect = httpx.TimeoutException("Failure")
            
            for i in range(3):
                await resilient_client.create_notification(notification_data)
            
            assert resilient_client.circuit_breaker.state == CircuitBreakerState.OPEN
            
            # Simulate timeout passage
            resilient_client.circuit_breaker.last_failure_time = time.time() - 10.0
            
            # Now make a successful call
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.side_effect = None
            mock_post.return_value = mock_response
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is True
            assert resilient_client.circuit_breaker.state == CircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_circuit_breaker_open(self, resilient_client, notification_data):
        """Test graceful degradation when circuit breaker is open."""
        # Manually open circuit breaker
        resilient_client.circuit_breaker.state = CircuitBreakerState.OPEN
        resilient_client.circuit_breaker.last_failure_time = time.time()
        
        # Call should return False but not raise exception
        result = await resilient_client.create_notification(notification_data)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_no_retry_on_unexpected_error(self, resilient_client, notification_data):
        """Test that unexpected errors don't trigger retries."""
        with patch.object(resilient_client.client, 'post') as mock_post:
            # Unexpected error should not be retried
            mock_post.side_effect = ValueError("Unexpected error")
            
            result = await resilient_client.create_notification(notification_data)
            
            assert result is False
            assert mock_post.call_count == 1  # No retries for unexpected errors


class TestNotificationClientIntegrationWithResilience:
    """Integration tests for notification client with resilience features."""
    
    @pytest.mark.asyncio
    async def test_task_assignment_notification_with_resilience(self):
        """Test task assignment notification with resilience features."""
        client = NotificationClient(
            base_url="http://test-service:8003",
            max_retries=1,
            base_delay=0.1
        )
        
        with patch.object(client.client, 'post') as mock_post:
            # First call fails, second succeeds
            mock_error_response = MagicMock()
            mock_error_response.status_code = 500
            mock_error_response.request = MagicMock()
            
            mock_success_response = MagicMock()
            mock_success_response.status_code = 201
            
            mock_post.side_effect = [mock_error_response, mock_success_response]
            
            result = await client.create_task_assigned_notification(
                assignee_id=2,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task",
                assigner_name="John Doe"
            )
            
            assert result is True
            assert mock_post.call_count == 2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_task_status_notification_with_resilience(self):
        """Test task status notification with resilience features."""
        client = NotificationClient(
            base_url="http://test-service:8003",
            max_retries=2,
            base_delay=0.1
        )
        
        with patch.object(client.client, 'post') as mock_post:
            # All calls fail
            mock_post.side_effect = httpx.ConnectError("Service unavailable")
            
            result = await client.create_task_status_notification(
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task",
                new_status="in_progress",
                updater_name="Jane Doe"
            )
            
            assert result is False
            assert mock_post.call_count == 3  # Initial + 2 retries
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_multiple_notifications_with_circuit_breaker(self):
        """Test multiple notifications with circuit breaker behavior."""
        client = NotificationClient(
            base_url="http://test-service:8003",
            max_retries=1,
            base_delay=0.1,
            circuit_breaker_failure_threshold=2
        )
        
        notification_data = NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification",
            type="task_assigned"
        )
        
        with patch.object(client.client, 'post') as mock_post:
            # All calls fail to trigger circuit breaker
            mock_post.side_effect = httpx.TimeoutException("Service down")
            
            # First two notifications should attempt HTTP calls
            result1 = await client.create_notification(notification_data)
            result2 = await client.create_notification(notification_data)
            
            assert result1 is False
            assert result2 is False
            assert client.circuit_breaker.state == CircuitBreakerState.OPEN
            
            # Third notification should be blocked by circuit breaker
            result3 = await client.create_notification(notification_data)
            assert result3 is False
            
            # Should have made 4 HTTP calls total (2 notifications * 2 attempts each)
            assert mock_post.call_count == 4
        
        await client.close()