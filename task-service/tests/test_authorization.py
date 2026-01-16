"""
Tests for task authorization and access control.
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId

from app.authorization import (
    TaskAuthorization, require_task_access, require_task_ownership,
    check_assignee_permission, get_user_task_filter
)
from app.models import TaskInDB, TaskStatus


class TestTaskAuthorization:
    """Test TaskAuthorization class methods."""
    
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
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def unassigned_task(self):
        """Task without assignee."""
        return TaskInDB(
            id=ObjectId(),
            title="Unassigned Task",
            description="Task without assignee",
            due_date=datetime.now() + timedelta(days=7),
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def completed_task(self):
        """Completed task for testing."""
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
    
    def test_can_view_task_creator(self, sample_task):
        """Test that creator can view task."""
        assert TaskAuthorization.can_view_task(sample_task, user_id=1) is True
    
    def test_can_view_task_assignee(self, sample_task):
        """Test that assignee can view task."""
        assert TaskAuthorization.can_view_task(sample_task, user_id=2) is True
    
    def test_can_view_task_unauthorized(self, sample_task):
        """Test that unauthorized user cannot view task."""
        assert TaskAuthorization.can_view_task(sample_task, user_id=3) is False
    
    def test_can_view_unassigned_task_creator(self, unassigned_task):
        """Test that creator can view unassigned task."""
        assert TaskAuthorization.can_view_task(unassigned_task, user_id=1) is True
    
    def test_can_view_unassigned_task_unauthorized(self, unassigned_task):
        """Test that unauthorized user cannot view unassigned task."""
        assert TaskAuthorization.can_view_task(unassigned_task, user_id=3) is False
    
    def test_can_edit_task_creator(self, sample_task):
        """Test that creator can edit task."""
        assert TaskAuthorization.can_edit_task(sample_task, user_id=1) is True
    
    def test_can_edit_task_assignee(self, sample_task):
        """Test that assignee can edit task."""
        assert TaskAuthorization.can_edit_task(sample_task, user_id=2) is True
    
    def test_can_edit_task_unauthorized(self, sample_task):
        """Test that unauthorized user cannot edit task."""
        assert TaskAuthorization.can_edit_task(sample_task, user_id=3) is False
    
    def test_can_delete_task_creator(self, sample_task):
        """Test that creator can delete task."""
        assert TaskAuthorization.can_delete_task(sample_task, user_id=1) is True
    
    def test_can_delete_task_assignee(self, sample_task):
        """Test that assignee cannot delete task."""
        assert TaskAuthorization.can_delete_task(sample_task, user_id=2) is False
    
    def test_can_delete_task_unauthorized(self, sample_task):
        """Test that unauthorized user cannot delete task."""
        assert TaskAuthorization.can_delete_task(sample_task, user_id=3) is False
    
    def test_can_assign_task_creator(self, sample_task):
        """Test that creator can assign task."""
        assert TaskAuthorization.can_assign_task(sample_task, user_id=1) is True
    
    def test_can_assign_task_assignee(self, sample_task):
        """Test that assignee cannot assign task."""
        assert TaskAuthorization.can_assign_task(sample_task, user_id=2) is False
    
    def test_can_assign_task_unauthorized(self, sample_task):
        """Test that unauthorized user cannot assign task."""
        assert TaskAuthorization.can_assign_task(sample_task, user_id=3) is False
    
    def test_can_change_status_creator(self, sample_task):
        """Test that creator can change status."""
        assert TaskAuthorization.can_change_status(sample_task, 1, TaskStatus.IN_PROGRESS) is True
    
    def test_can_change_status_assignee(self, sample_task):
        """Test that assignee can change status."""
        assert TaskAuthorization.can_change_status(sample_task, 2, TaskStatus.IN_PROGRESS) is True
    
    def test_can_change_status_unauthorized(self, sample_task):
        """Test that unauthorized user cannot change status."""
        assert TaskAuthorization.can_change_status(sample_task, 3, TaskStatus.IN_PROGRESS) is False
    
    def test_can_reopen_completed_task_creator(self, completed_task):
        """Test that creator can reopen completed task."""
        assert TaskAuthorization.can_change_status(completed_task, 1, TaskStatus.IN_PROGRESS) is True
    
    def test_cannot_reopen_completed_task_assignee(self, completed_task):
        """Test that assignee cannot reopen completed task."""
        assert TaskAuthorization.can_change_status(completed_task, 2, TaskStatus.IN_PROGRESS) is False
    
    def test_can_complete_task_assignee(self, sample_task):
        """Test that assignee can complete task."""
        assert TaskAuthorization.can_change_status(sample_task, 2, TaskStatus.DONE) is True
    
    def test_filter_user_accessible_tasks(self, sample_task, unassigned_task):
        """Test filtering tasks by user access."""
        tasks = [sample_task, unassigned_task]
        
        # Creator can see both tasks
        creator_tasks = TaskAuthorization.filter_user_accessible_tasks(tasks, user_id=1)
        assert len(creator_tasks) == 2
        
        # Assignee can only see assigned task
        assignee_tasks = TaskAuthorization.filter_user_accessible_tasks(tasks, user_id=2)
        assert len(assignee_tasks) == 1
        assert assignee_tasks[0].id == sample_task.id
        
        # Unauthorized user sees no tasks
        unauthorized_tasks = TaskAuthorization.filter_user_accessible_tasks(tasks, user_id=3)
        assert len(unauthorized_tasks) == 0
    
    def test_validate_task_access_success(self, sample_task):
        """Test successful task access validation."""
        # Should not raise exception
        TaskAuthorization.validate_task_access(sample_task, user_id=1, action="view")
        TaskAuthorization.validate_task_access(sample_task, user_id=2, action="edit")
    
    def test_validate_task_access_permission_denied(self, sample_task):
        """Test task access validation with permission denied."""
        with pytest.raises(PermissionError, match="does not have permission"):
            TaskAuthorization.validate_task_access(sample_task, user_id=3, action="view")
    
    def test_validate_task_access_task_not_found(self):
        """Test task access validation with no task."""
        with pytest.raises(ValueError, match="Task not found"):
            TaskAuthorization.validate_task_access(None, user_id=1, action="view")
    
    def test_validate_task_access_invalid_action(self, sample_task):
        """Test task access validation with invalid action."""
        with pytest.raises(ValueError, match="Unknown action"):
            TaskAuthorization.validate_task_access(sample_task, user_id=1, action="invalid")
    
    def test_validate_status_change_success(self, sample_task):
        """Test successful status change validation."""
        # Should not raise exception
        TaskAuthorization.validate_status_change(sample_task, 1, TaskStatus.IN_PROGRESS)
        TaskAuthorization.validate_status_change(sample_task, 2, TaskStatus.DONE)
    
    def test_validate_status_change_permission_denied(self, sample_task):
        """Test status change validation with permission denied."""
        with pytest.raises(PermissionError, match="cannot change task status"):
            TaskAuthorization.validate_status_change(sample_task, 3, TaskStatus.IN_PROGRESS)
    
    def test_validate_status_change_reopen_denied(self, completed_task):
        """Test that assignee cannot reopen completed task."""
        with pytest.raises(PermissionError, match="cannot change task status"):
            TaskAuthorization.validate_status_change(completed_task, 2, TaskStatus.IN_PROGRESS)


class TestAuthorizationHelpers:
    """Test authorization helper functions."""
    
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
            assignee_id=2,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_require_task_access_success(self, sample_task):
        """Test successful task access requirement."""
        result = require_task_access(sample_task, user_id=1, action="view")
        assert result == sample_task
    
    def test_require_task_access_denied(self, sample_task):
        """Test task access requirement with permission denied."""
        with pytest.raises(PermissionError):
            require_task_access(sample_task, user_id=3, action="view")
    
    def test_require_task_ownership_success(self, sample_task):
        """Test successful task ownership requirement."""
        result = require_task_ownership(sample_task, user_id=1)
        assert result == sample_task
    
    def test_require_task_ownership_denied(self, sample_task):
        """Test task ownership requirement with permission denied."""
        with pytest.raises(PermissionError, match="is not the owner"):
            require_task_ownership(sample_task, user_id=2)
    
    def test_require_task_ownership_not_found(self):
        """Test task ownership requirement with no task."""
        with pytest.raises(ValueError, match="Task not found"):
            require_task_ownership(None, user_id=1)
    
    def test_check_assignee_permission_success(self, sample_task):
        """Test successful assignee permission check."""
        # Should not raise exception
        check_assignee_permission(sample_task, user_id=1, assignee_id=3)
    
    def test_check_assignee_permission_denied(self, sample_task):
        """Test assignee permission check with permission denied."""
        with pytest.raises(PermissionError, match="cannot assign task"):
            check_assignee_permission(sample_task, user_id=2, assignee_id=3)
    
    def test_check_assignee_permission_none_assignee(self, sample_task):
        """Test assignee permission check with None assignee."""
        # Should not raise exception when assignee_id is None
        check_assignee_permission(sample_task, user_id=2, assignee_id=None)
    
    def test_get_user_task_filter(self):
        """Test user task filter generation."""
        filter_dict = get_user_task_filter(user_id=1)
        
        expected = {
            "$or": [
                {"creator_id": 1},
                {"assignee_id": 1}
            ]
        }
        
        assert filter_dict == expected