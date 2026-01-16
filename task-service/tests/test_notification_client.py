"""
Unit tests for the notification client functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.notification_client import (
    NotificationClient,
    NotificationData,
    get_notification_client,
    close_notification_client
)


class TestNotificationData:
    """Test cases for NotificationData model."""
    
    def test_notification_data_creation(self):
        """Test creating a NotificationData instance."""
        data = NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification",
            type="task_assigned"
        )
        
        assert data.user_id == 1
        assert data.task_id == "507f1f77bcf86cd799439011"
        assert data.message == "Test notification"
        assert data.type == "task_assigned"
    
    def test_notification_data_model_dump(self):
        """Test converting NotificationData to dictionary."""
        data = NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification",
            type="task_assigned"
        )
        
        result = data.model_dump()
        expected = {
            "user_id": 1,
            "task_id": "507f1f77bcf86cd799439011",
            "message": "Test notification",
            "type": "task_assigned"
        }
        
        assert result == expected


class TestNotificationClient:
    """Test cases for NotificationClient."""
    
    @pytest.fixture
    def client(self):
        """Create a NotificationClient instance for testing."""
        return NotificationClient(base_url="http://test-notification-service:8003")
    
    @pytest.fixture
    def notification_data(self):
        """Create test notification data."""
        return NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Test notification",
            type="task_assigned"
        )
    
    def test_client_initialization_default_url(self):
        """Test client initialization with default URL."""
        with patch.dict('os.environ', {}, clear=True):
            client = NotificationClient()
            assert client.base_url == "http://notification-service:8003"
            assert client.timeout == 10.0
    
    def test_client_initialization_env_url(self):
        """Test client initialization with environment variable URL."""
        with patch.dict('os.environ', {'NOTIFICATION_SERVICE_URL': 'http://custom:8003'}):
            client = NotificationClient()
            assert client.base_url == "http://custom:8003"
    
    def test_client_initialization_custom_url(self):
        """Test client initialization with custom URL."""
        client = NotificationClient(base_url="http://custom:8003", timeout=5.0)
        assert client.base_url == "http://custom:8003"
        assert client.timeout == 5.0
    
    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test closing the HTTP client."""
        mock_client = AsyncMock()
        client.client = mock_client
        
        await client.close()
        mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_notification_success(self, client, notification_data):
        """Test successful notification creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch.object(client.client, 'post', return_value=mock_response) as mock_post:
            result = await client.create_notification(notification_data)
            
            assert result is True
            mock_post.assert_called_once_with(
                "http://test-notification-service:8003/api/v1/notifications",
                json=notification_data.model_dump(),
                headers={"Content-Type": "application/json"}
            )
    
    @pytest.mark.asyncio
    async def test_create_notification_failure(self, client, notification_data):
        """Test notification creation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.create_notification(notification_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_notification_timeout(self, client, notification_data):
        """Test notification creation with timeout."""
        with patch.object(client.client, 'post', side_effect=httpx.TimeoutException("Timeout")):
            result = await client.create_notification(notification_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_notification_connection_error(self, client, notification_data):
        """Test notification creation with connection error."""
        with patch.object(client.client, 'post', side_effect=httpx.ConnectError("Connection failed")):
            result = await client.create_notification(notification_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_notification_unexpected_error(self, client, notification_data):
        """Test notification creation with unexpected error."""
        with patch.object(client.client, 'post', side_effect=Exception("Unexpected error")):
            result = await client.create_notification(notification_data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_task_assigned_notification(self, client):
        """Test creating a task assignment notification."""
        with patch.object(client, 'create_notification', return_value=True) as mock_create:
            result = await client.create_task_assigned_notification(
                assignee_id=2,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task",
                assigner_name="John Doe"
            )
            
            assert result is True
            mock_create.assert_called_once()
            
            # Check the notification data passed to create_notification
            call_args = mock_create.call_args[0][0]
            assert call_args.user_id == 2
            assert call_args.task_id == "507f1f77bcf86cd799439011"
            assert call_args.type == "task_assigned"
            assert "Test Task" in call_args.message
            assert "John Doe" in call_args.message
    
    @pytest.mark.asyncio
    async def test_create_task_assigned_notification_default_assigner(self, client):
        """Test creating a task assignment notification with default assigner."""
        with patch.object(client, 'create_notification', return_value=True) as mock_create:
            result = await client.create_task_assigned_notification(
                assignee_id=2,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task"
            )
            
            assert result is True
            call_args = mock_create.call_args[0][0]
            assert "System" in call_args.message
    
    @pytest.mark.asyncio
    async def test_create_task_status_notification(self, client):
        """Test creating a task status update notification."""
        with patch.object(client, 'create_notification', return_value=True) as mock_create:
            result = await client.create_task_status_notification(
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task",
                new_status="in_progress",
                updater_name="Jane Doe"
            )
            
            assert result is True
            mock_create.assert_called_once()
            
            # Check the notification data passed to create_notification
            call_args = mock_create.call_args[0][0]
            assert call_args.user_id == 1
            assert call_args.task_id == "507f1f77bcf86cd799439011"
            assert call_args.type == "task_updated"
            assert "Test Task" in call_args.message
            assert "In Progress" in call_args.message  # Status should be formatted
            assert "Jane Doe" in call_args.message
    
    @pytest.mark.asyncio
    async def test_create_task_status_notification_default_updater(self, client):
        """Test creating a task status notification with default updater."""
        with patch.object(client, 'create_notification', return_value=True) as mock_create:
            result = await client.create_task_status_notification(
                user_id=1,
                task_id="507f1f77bcf86cd799439011",
                task_title="Test Task",
                new_status="done"
            )
            
            assert result is True
            call_args = mock_create.call_args[0][0]
            assert "System" in call_args.message
            assert "Done" in call_args.message  # Status should be formatted


class TestGlobalNotificationClient:
    """Test cases for global notification client functions."""
    
    @pytest.mark.asyncio
    async def test_get_notification_client_singleton(self):
        """Test that get_notification_client returns the same instance."""
        # Clear any existing global client
        await close_notification_client()
        
        client1 = get_notification_client()
        client2 = get_notification_client()
        
        assert client1 is client2
        
        # Clean up
        await close_notification_client()
    
    @pytest.mark.asyncio
    async def test_close_notification_client(self):
        """Test closing the global notification client."""
        # Get a client instance
        client = get_notification_client()
        
        with patch.object(client, 'close') as mock_close:
            await close_notification_client()
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_notification_client_no_instance(self):
        """Test closing when no global client exists."""
        # Ensure no global client exists
        await close_notification_client()
        
        # This should not raise an exception
        await close_notification_client()


class TestNotificationClientIntegration:
    """Integration tests for notification client with service communication."""
    
    @pytest.mark.asyncio
    async def test_notification_client_with_real_http_client(self):
        """Test notification client with actual HTTP client (mocked responses)."""
        client = NotificationClient(base_url="http://test-service:8003")
        
        notification_data = NotificationData(
            user_id=1,
            task_id="507f1f77bcf86cd799439011",
            message="Integration test notification",
            type="task_assigned"
        )
        
        # Mock the HTTP response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            
            result = await client.create_notification(notification_data)
            
            assert result is True
            mock_post.assert_called_once_with(
                "http://test-service:8003/api/v1/notifications",
                json=notification_data.model_dump(),
                headers={"Content-Type": "application/json"}
            )
        
        await client.close()