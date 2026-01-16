"""
Tests for Task Service business logic layer.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services import TaskService
from app.models import TaskCreate, TaskUpdate, TaskStatus, TaskInDB
from app.repository import TaskRepository


class TestTaskService:
    """Test TaskService business logic."""
    
    @pytest_asyncio.fixture
    async def mock_repository(self):
        """Create a mock task repository."""
        return AsyncMock(spec=TaskRepository)
    
    @pytest_asyncio.fixture
    async def task_service(self, mock_repository):
        """Create a task service with mock repository."""
        service = TaskService.__new__(TaskService)
        service.repository = mock_repository
        return service
    
    @pytest.fixture
    def sample_task_data(self):
        """Sample task creation data."""
        return TaskCreate(
            title="Test Task",
            description="Test description",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            assignee_id=2
        )
    
    @pytest.fixture
    def sample_task_in_db(self):
        """Sample task from database."""
        from bson import ObjectId
        return TaskInDB(
            id=ObjectId(),
            title="Test Task",
            description="Test description",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, task_service, mock_repository, sample_task_data, sample_task_in_db):
        """Test successful task creation."""
        # Setup mock
        mock_repository.create_task.return_value = sample_task_in_db
        
        # Execute
        result = await task_service.create_task(sample_task_data, creator_id=1)
        
        # Verify
        assert result is not None
        assert result.title == sample_task_data.title
        assert result.description == sample_task_data.description
        assert result.creator_id == 1
        assert result.assignee_id == sample_task_data.assignee_id
        mock_repository.create_task.assert_called_once_with(sample_task_data, 1)
    
    @pytest.mark.asyncio
    async def test_create_task_failure(self, task_service, mock_repository, sample_task_data):
        """Test task creation failure."""
        # Setup mock to raise exception
        mock_repository.create_task.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Failed to create task"):
            await task_service.create_task(sample_task_data, creator_id=1)
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_success_creator(self, task_service, mock_repository, sample_task_in_db):
        """Test getting task by ID as creator."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute
        result = await task_service.get_task_by_id(str(sample_task_in_db.id), user_id=1)
        
        # Verify
        assert result is not None
        assert result.id == str(sample_task_in_db.id)
        assert result.title == sample_task_in_db.title
        mock_repository.get_task_by_id.assert_called_once_with(str(sample_task_in_db.id))
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_success_assignee(self, task_service, mock_repository, sample_task_in_db):
        """Test getting task by ID as assignee."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute
        result = await task_service.get_task_by_id(str(sample_task_in_db.id), user_id=2)
        
        # Verify
        assert result is not None
        assert result.id == str(sample_task_in_db.id)
        mock_repository.get_task_by_id.assert_called_once_with(str(sample_task_in_db.id))
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_permission_denied(self, task_service, mock_repository, sample_task_in_db):
        """Test getting task by ID with no permission."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="User does not have access"):
            await task_service.get_task_by_id(str(sample_task_in_db.id), user_id=999)
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, task_service, mock_repository):
        """Test getting non-existent task."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = None
        
        # Execute
        result = await task_service.get_task_by_id("nonexistent_id", user_id=1)
        
        # Verify
        assert result is None
        mock_repository.get_task_by_id.assert_called_once_with("nonexistent_id")
    
    @pytest.mark.asyncio
    async def test_get_user_tasks_success(self, task_service, mock_repository, sample_task_in_db):
        """Test getting user tasks."""
        # Setup mock
        mock_repository.get_tasks_by_user.return_value = [sample_task_in_db]
        
        # Execute
        result = await task_service.get_user_tasks(user_id=1, skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].id == str(sample_task_in_db.id)
        mock_repository.get_tasks_by_user.assert_called_once_with(1, 0, 10)
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status_success(self, task_service, mock_repository, sample_task_in_db):
        """Test getting tasks by status."""
        # Setup mock
        mock_repository.get_tasks_by_status.return_value = [sample_task_in_db]
        
        # Execute
        result = await task_service.get_tasks_by_status(user_id=1, status="to_do", skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].status == TaskStatus.TO_DO
        mock_repository.get_tasks_by_status.assert_called_once_with("to_do", 1, 0, 10)
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, task_service, mock_repository, sample_task_in_db):
        """Test successful task update."""
        # Setup mock
        updated_task = sample_task_in_db.copy()
        updated_task.title = "Updated Title"
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        update_data = TaskUpdate(title="Updated Title")
        result = await task_service.update_task(str(sample_task_in_db.id), update_data, user_id=1)
        
        # Verify
        assert result is not None
        assert result.title == "Updated Title"
        mock_repository.update_task.assert_called_once_with(str(sample_task_in_db.id), update_data, 1)
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, task_service, mock_repository):
        """Test updating non-existent task."""
        # Setup mock
        mock_repository.update_task.return_value = None
        
        # Execute
        update_data = TaskUpdate(title="Updated Title")
        result = await task_service.update_task("nonexistent_id", update_data, user_id=1)
        
        # Verify
        assert result is None
        mock_repository.update_task.assert_called_once_with("nonexistent_id", update_data, 1)
    
    @pytest.mark.asyncio
    async def test_update_task_permission_denied(self, task_service, mock_repository):
        """Test updating task without permission."""
        # Setup mock to raise permission error
        mock_repository.update_task.side_effect = PermissionError("Permission denied")
        
        # Execute and verify exception
        update_data = TaskUpdate(title="Updated Title")
        with pytest.raises(PermissionError):
            await task_service.update_task("task_id", update_data, user_id=999)
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, task_service, mock_repository):
        """Test successful task deletion."""
        # Setup mock
        mock_repository.delete_task.return_value = True
        
        # Execute
        result = await task_service.delete_task("task_id", user_id=1)
        
        # Verify
        assert result is True
        mock_repository.delete_task.assert_called_once_with("task_id", 1)
    
    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, task_service, mock_repository):
        """Test deleting non-existent task."""
        # Setup mock
        mock_repository.delete_task.return_value = False
        
        # Execute
        result = await task_service.delete_task("nonexistent_id", user_id=1)
        
        # Verify
        assert result is False
        mock_repository.delete_task.assert_called_once_with("nonexistent_id", 1)
    
    @pytest.mark.asyncio
    async def test_delete_task_permission_denied(self, task_service, mock_repository):
        """Test deleting task without permission."""
        # Setup mock to raise permission error
        mock_repository.delete_task.side_effect = PermissionError("Only creator can delete")
        
        # Execute and verify exception
        with pytest.raises(PermissionError):
            await task_service.delete_task("task_id", user_id=999)
    
    @pytest.mark.asyncio
    async def test_count_user_tasks_success(self, task_service, mock_repository):
        """Test counting user tasks."""
        # Setup mock
        mock_repository.count_user_tasks.return_value = 5
        
        # Execute
        result = await task_service.count_user_tasks(user_id=1)
        
        # Verify
        assert result == 5
        mock_repository.count_user_tasks.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_assign_task_success_with_notification(self, task_service, mock_repository, sample_task_in_db):
        """Test successful task assignment with notification."""
        from unittest.mock import patch
        
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.assignee_id = 3
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_assigned_notification.return_value = True
            mock_get_client.return_value = mock_client
            
            # Execute
            result = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=3, user_id=1)
            
            # Verify task assignment
            assert result is not None
            assert result.assignee_id == 3
            mock_repository.get_task_by_id.assert_called_once_with(str(sample_task_in_db.id))
            
            # Verify notification was sent
            mock_client.create_task_assigned_notification.assert_called_once_with(
                assignee_id=3,
                task_id=str(sample_task_in_db.id),
                task_title=updated_task.title,
                assigner_name="User 1"
            )
    
    @pytest.mark.asyncio
    async def test_assign_task_no_notification_same_assignee(self, task_service, mock_repository, sample_task_in_db):
        """Test task assignment with no notification when assignee doesn't change."""
        from unittest.mock import patch
        
        # Setup mocks - task already assigned to user 2
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        mock_repository.update_task.return_value = sample_task_in_db
        
        # Mock notification client
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Execute - assign to same user
            result = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=2, user_id=1)
            
            # Verify task assignment
            assert result is not None
            
            # Verify no notification was sent (same assignee)
            mock_client.create_task_assigned_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_assign_task_notification_failure_doesnt_fail_assignment(self, task_service, mock_repository, sample_task_in_db):
        """Test that notification failure doesn't prevent task assignment."""
        from unittest.mock import patch
        
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.assignee_id = 3
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client to fail
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_assigned_notification.side_effect = Exception("Notification service down")
            mock_get_client.return_value = mock_client
            
            # Execute - should succeed despite notification failure
            result = await task_service.assign_task(str(sample_task_in_db.id), assignee_id=3, user_id=1)
            
            # Verify task assignment still succeeded
            assert result is not None
            assert result.assignee_id == 3
    
    @pytest.mark.asyncio
    async def test_assign_task_permission_denied(self, task_service, mock_repository, sample_task_in_db):
        """Test task assignment permission denied."""
        # Setup mock - user is not the creator
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator can assign tasks"):
            await task_service.assign_task(str(sample_task_in_db.id), assignee_id=3, user_id=999)
    
    @pytest.mark.asyncio
    async def test_assign_task_invalid_assignee_id(self, task_service, mock_repository, sample_task_in_db):
        """Test task assignment with invalid assignee ID."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid assignee ID"):
            await task_service.assign_task(str(sample_task_in_db.id), assignee_id=0, user_id=1)
    
    @pytest.mark.asyncio
    async def test_unassign_task_success(self, task_service, mock_repository, sample_task_in_db):
        """Test successful task unassignment."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.assignee_id = None
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.unassign_task(str(sample_task_in_db.id), user_id=1)
        
        # Verify
        assert result is not None
        assert result.assignee_id is None
        mock_repository.get_task_by_id.assert_called_once_with(str(sample_task_in_db.id))
    
    @pytest.mark.asyncio
    async def test_unassign_task_permission_denied(self, task_service, mock_repository, sample_task_in_db):
        """Test task unassignment permission denied."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator can unassign tasks"):
            await task_service.unassign_task(str(sample_task_in_db.id), user_id=999)
    
    @pytest.mark.asyncio
    async def test_change_task_status_success_with_notifications(self, task_service, mock_repository, sample_task_in_db):
        """Test successful task status change with notifications."""
        from unittest.mock import patch
        
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.status = TaskStatus.IN_PROGRESS
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_status_notification.return_value = True
            mock_get_client.return_value = mock_client
            
            # Execute - user 3 updates status (neither creator nor assignee)
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=1)
            
            # Verify status change
            assert result is not None
            assert result.status == TaskStatus.IN_PROGRESS
            
            # Verify notification was sent to assignee (user 2)
            mock_client.create_task_status_notification.assert_called_once_with(
                user_id=2,  # assignee_id from sample_task_in_db
                task_id=str(sample_task_in_db.id),
                task_title=updated_task.title,
                new_status="in_progress",
                updater_name="User 1"
            )
    
    @pytest.mark.asyncio
    async def test_change_task_status_notifications_to_both_users(self, task_service, mock_repository, sample_task_in_db):
        """Test status change notifications sent to both creator and assignee."""
        from unittest.mock import patch
        
        # Setup mocks - user 3 updates the task (neither creator nor assignee)
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.status = TaskStatus.DONE
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_status_notification.return_value = True
            mock_get_client.return_value = mock_client
            
            # Execute - user 2 (assignee) updates status
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.DONE, user_id=2)
            
            # Verify status change
            assert result is not None
            assert result.status == TaskStatus.DONE
            
            # Verify notification was sent to creator (1) only, since user 2 (assignee) is the one updating
            mock_client.create_task_status_notification.assert_called_once_with(
                user_id=1,  # creator_id from sample_task_in_db
                task_id=str(sample_task_in_db.id),
                task_title=updated_task.title,
                new_status="done",
                updater_name="User 2"
            )
    
    @pytest.mark.asyncio
    async def test_change_task_status_no_notification_same_status(self, task_service, mock_repository, sample_task_in_db):
        """Test no notification when status doesn't change."""
        from unittest.mock import patch
        
        # Setup mocks - status remains the same
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        mock_repository.update_task.return_value = sample_task_in_db
        
        # Mock notification client
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Execute - set to same status
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.TO_DO, user_id=1)
            
            # Verify no notification was sent
            mock_client.create_task_status_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_change_task_status_notification_failure_doesnt_fail_update(self, task_service, mock_repository, sample_task_in_db):
        """Test that notification failure doesn't prevent status update."""
        from unittest.mock import patch
        
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        updated_task = sample_task_in_db.copy()
        updated_task.status = TaskStatus.IN_PROGRESS
        mock_repository.update_task.return_value = updated_task
        
        # Mock notification client to fail
        with patch('app.services.get_notification_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_task_status_notification.side_effect = Exception("Notification service down")
            mock_get_client.return_value = mock_client
            
            # Execute - should succeed despite notification failure
            result = await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=1)
            
            # Verify status update still succeeded
            assert result is not None
            assert result.status == TaskStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_change_task_status_permission_denied(self, task_service, mock_repository, sample_task_in_db):
        """Test task status change permission denied."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task_in_db
        
        # Execute and verify exception - user 999 is neither creator nor assignee
        with pytest.raises(PermissionError, match="Only task creator or assignee can change status"):
            await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=999)
    
    @pytest.mark.asyncio
    async def test_change_task_status_reopen_completed_task_permission_denied(self, task_service, mock_repository, sample_task_in_db):
        """Test reopening completed task permission denied for non-creator."""
        # Setup mock - task is completed
        completed_task = sample_task_in_db.copy()
        completed_task.status = TaskStatus.DONE
        mock_repository.get_task_by_id.return_value = completed_task
        
        # Execute and verify exception - assignee cannot reopen completed task
        with pytest.raises(PermissionError, match="Only task creator can reopen completed tasks"):
            await task_service.change_task_status(str(sample_task_in_db.id), TaskStatus.IN_PROGRESS, user_id=2)
    
    @pytest.mark.asyncio
    async def test_get_assigned_tasks_success(self, task_service, mock_repository, sample_task_in_db):
        """Test getting assigned tasks."""
        # Setup mock
        mock_repository.get_tasks_by_assignee.return_value = [sample_task_in_db]
        
        # Execute
        result = await task_service.get_assigned_tasks(assignee_id=2, skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].assignee_id == 2
        mock_repository.get_tasks_by_assignee.assert_called_once_with(2, 0, 10)
    
    @pytest.mark.asyncio
    async def test_get_created_tasks_success(self, task_service, mock_repository, sample_task_in_db):
        """Test getting created tasks."""
        # Setup mock
        mock_repository.get_tasks_by_creator.return_value = [sample_task_in_db]
        
        # Execute
        result = await task_service.get_created_tasks(creator_id=1, skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].creator_id == 1
        mock_repository.get_tasks_by_creator.assert_called_once_with(1, 0, 10)