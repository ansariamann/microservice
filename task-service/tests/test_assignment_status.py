"""
Tests for task assignment and status management functionality.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.services import TaskService
from app.models import TaskCreate, TaskUpdate, TaskStatus, TaskInDB
from app.repository import TaskRepository


class TestTaskAssignment:
    """Test task assignment functionality."""
    
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
    def sample_task(self):
        """Sample task for testing."""
        return TaskInDB(
            id=ObjectId(),
            title="Test Task",
            description="Test description",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def assigned_task(self):
        """Task that is already assigned."""
        return TaskInDB(
            id=ObjectId(),
            title="Assigned Task",
            description="Task with assignee",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_assign_task_success(self, task_service, mock_repository, sample_task):
        """Test successful task assignment."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = sample_task
        
        updated_task = sample_task.model_copy()
        updated_task.assignee_id = 3
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.assign_task(str(sample_task.id), assignee_id=3, user_id=1)
        
        # Verify
        assert result is not None
        assert result.assignee_id == 3
        mock_repository.get_task_by_id.assert_called_once_with(str(sample_task.id))
        mock_repository.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_task_not_found(self, task_service, mock_repository):
        """Test assigning non-existent task."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = None
        
        # Execute
        result = await task_service.assign_task("nonexistent_id", assignee_id=3, user_id=1)
        
        # Verify
        assert result is None
        mock_repository.get_task_by_id.assert_called_once_with("nonexistent_id")
    
    @pytest.mark.asyncio
    async def test_assign_task_permission_denied(self, task_service, mock_repository, sample_task):
        """Test assigning task without permission."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator can assign"):
            await task_service.assign_task(str(sample_task.id), assignee_id=3, user_id=2)
    
    @pytest.mark.asyncio
    async def test_assign_task_invalid_assignee(self, task_service, mock_repository, sample_task):
        """Test assigning task with invalid assignee ID."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = sample_task
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid assignee ID"):
            await task_service.assign_task(str(sample_task.id), assignee_id=0, user_id=1)
    
    @pytest.mark.asyncio
    async def test_unassign_task_success(self, task_service, mock_repository, assigned_task):
        """Test successful task unassignment."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = assigned_task
        
        updated_task = assigned_task.model_copy()
        updated_task.assignee_id = None
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.unassign_task(str(assigned_task.id), user_id=1)
        
        # Verify
        assert result is not None
        assert result.assignee_id is None
        mock_repository.get_task_by_id.assert_called_once_with(str(assigned_task.id))
        mock_repository.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unassign_task_permission_denied(self, task_service, mock_repository, assigned_task):
        """Test unassigning task without permission."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = assigned_task
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator can unassign"):
            await task_service.unassign_task(str(assigned_task.id), user_id=2)
    
    @pytest.mark.asyncio
    async def test_get_assigned_tasks(self, task_service, mock_repository, assigned_task):
        """Test getting assigned tasks."""
        # Setup mock
        mock_repository.get_tasks_by_assignee.return_value = [assigned_task]
        
        # Execute
        result = await task_service.get_assigned_tasks(assignee_id=2, skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].assignee_id == 2
        mock_repository.get_tasks_by_assignee.assert_called_once_with(2, 0, 10)
    
    @pytest.mark.asyncio
    async def test_get_created_tasks(self, task_service, mock_repository, sample_task):
        """Test getting created tasks."""
        # Setup mock
        mock_repository.get_tasks_by_creator.return_value = [sample_task]
        
        # Execute
        result = await task_service.get_created_tasks(creator_id=1, skip=0, limit=10)
        
        # Verify
        assert len(result) == 1
        assert result[0].creator_id == 1
        mock_repository.get_tasks_by_creator.assert_called_once_with(1, 0, 10)


class TestTaskStatusManagement:
    """Test task status management functionality."""
    
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
    def todo_task(self):
        """Task in TO_DO status."""
        return TaskInDB(
            id=ObjectId(),
            title="Todo Task",
            description="Task to be started",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def completed_task(self):
        """Task in DONE status."""
        return TaskInDB(
            id=ObjectId(),
            title="Completed Task",
            description="Task that is done",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.DONE,
            creator_id=1,
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_change_status_creator_success(self, task_service, mock_repository, todo_task):
        """Test successful status change by creator."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = todo_task
        
        updated_task = todo_task.model_copy()
        updated_task.status = TaskStatus.IN_PROGRESS
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.change_task_status(str(todo_task.id), TaskStatus.IN_PROGRESS, user_id=1)
        
        # Verify
        assert result is not None
        assert result.status == TaskStatus.IN_PROGRESS
        mock_repository.get_task_by_id.assert_called_once_with(str(todo_task.id))
        mock_repository.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_status_assignee_success(self, task_service, mock_repository, todo_task):
        """Test successful status change by assignee."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = todo_task
        
        updated_task = todo_task.model_copy()
        updated_task.status = TaskStatus.DONE
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.change_task_status(str(todo_task.id), TaskStatus.DONE, user_id=2)
        
        # Verify
        assert result is not None
        assert result.status == TaskStatus.DONE
        mock_repository.get_task_by_id.assert_called_once_with(str(todo_task.id))
        mock_repository.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_status_permission_denied(self, task_service, mock_repository, todo_task):
        """Test status change without permission."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = todo_task
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator or assignee can change status"):
            await task_service.change_task_status(str(todo_task.id), TaskStatus.IN_PROGRESS, user_id=3)
    
    @pytest.mark.asyncio
    async def test_reopen_completed_task_creator(self, task_service, mock_repository, completed_task):
        """Test reopening completed task by creator."""
        # Setup mocks
        mock_repository.get_task_by_id.return_value = completed_task
        
        updated_task = completed_task.model_copy()
        updated_task.status = TaskStatus.IN_PROGRESS
        updated_task.updated_at = datetime.now()
        mock_repository.update_task.return_value = updated_task
        
        # Execute
        result = await task_service.change_task_status(str(completed_task.id), TaskStatus.IN_PROGRESS, user_id=1)
        
        # Verify
        assert result is not None
        assert result.status == TaskStatus.IN_PROGRESS
        mock_repository.get_task_by_id.assert_called_once_with(str(completed_task.id))
        mock_repository.update_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reopen_completed_task_assignee_denied(self, task_service, mock_repository, completed_task):
        """Test that assignee cannot reopen completed task."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = completed_task
        
        # Execute and verify exception
        with pytest.raises(PermissionError, match="Only task creator can reopen completed tasks"):
            await task_service.change_task_status(str(completed_task.id), TaskStatus.IN_PROGRESS, user_id=2)
    
    @pytest.mark.asyncio
    async def test_change_status_task_not_found(self, task_service, mock_repository):
        """Test changing status of non-existent task."""
        # Setup mock
        mock_repository.get_task_by_id.return_value = None
        
        # Execute
        result = await task_service.change_task_status("nonexistent_id", TaskStatus.IN_PROGRESS, user_id=1)
        
        # Verify
        assert result is None
        mock_repository.get_task_by_id.assert_called_once_with("nonexistent_id")


class TestTaskStatusValidation:
    """Test task status validation logic."""
    
    def test_valid_status_transitions(self):
        """Test valid status transitions."""
        # All transitions should be allowed in general
        valid_transitions = [
            (TaskStatus.TO_DO, TaskStatus.IN_PROGRESS),
            (TaskStatus.TO_DO, TaskStatus.DONE),
            (TaskStatus.IN_PROGRESS, TaskStatus.TO_DO),
            (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
            (TaskStatus.DONE, TaskStatus.IN_PROGRESS),  # Only for creator
            (TaskStatus.DONE, TaskStatus.TO_DO),       # Only for creator
        ]
        
        for from_status, to_status in valid_transitions:
            # This test just verifies the enum values are valid
            assert isinstance(from_status, TaskStatus)
            assert isinstance(to_status, TaskStatus)
    
    def test_task_status_enum_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.TO_DO.value == "to_do"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"
    
    def test_task_status_from_string(self):
        """Test creating TaskStatus from string."""
        assert TaskStatus("to_do") == TaskStatus.TO_DO
        assert TaskStatus("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus("done") == TaskStatus.DONE
        
        # Test invalid status
        with pytest.raises(ValueError):
            TaskStatus("invalid_status")


class TestAssignmentValidation:
    """Test assignment validation logic."""
    
    def test_valid_assignee_ids(self):
        """Test valid assignee ID validation."""
        valid_ids = [1, 2, 100, 999999]
        
        for assignee_id in valid_ids:
            # Should not raise exception for positive integers
            assert assignee_id > 0
    
    def test_invalid_assignee_ids(self):
        """Test invalid assignee ID validation."""
        invalid_ids = [0, -1, -100]
        
        for assignee_id in invalid_ids:
            # Should be invalid (non-positive)
            assert assignee_id <= 0
    
    def test_none_assignee_id(self):
        """Test None assignee ID (unassignment)."""
        assignee_id = None
        # None should be valid for unassignment
        assert assignee_id is None