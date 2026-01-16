"""
Tests for Task Repository MongoDB operations.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from bson import ObjectId

from app.repository import TaskRepository
from app.models import TaskCreate, TaskUpdate, TaskStatus


class TestTaskRepository:
    """Test TaskRepository database operations."""
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_repository, sample_task_data, creator_id):
        """Test creating a new task."""
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        assert created_task is not None
        assert created_task.title == sample_task_data.title
        assert created_task.description == sample_task_data.description
        assert created_task.creator_id == creator_id
        assert created_task.assignee_id == sample_task_data.assignee_id
        assert created_task.status == sample_task_data.status
        assert created_task.created_at is not None
        assert created_task.updated_at is not None
        assert isinstance(created_task.id, ObjectId)
    
    @pytest.mark.asyncio
    async def test_create_task_without_assignee(self, task_repository, sample_task_data_no_assignee, creator_id):
        """Test creating a task without assignee."""
        created_task = await task_repository.create_task(sample_task_data_no_assignee, creator_id)
        
        assert created_task is not None
        assert created_task.assignee_id is None
        assert created_task.creator_id == creator_id
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, task_repository, sample_task_data, creator_id):
        """Test retrieving a task by ID."""
        # Create a task first
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        # Retrieve the task
        retrieved_task = await task_repository.get_task_by_id(str(created_task.id))
        
        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.title == created_task.title
        assert retrieved_task.creator_id == created_task.creator_id
    
    @pytest.mark.asyncio
    async def test_get_task_by_invalid_id(self, task_repository):
        """Test retrieving task with invalid ID."""
        result = await task_repository.get_task_by_id("invalid_id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_task_by_nonexistent_id(self, task_repository):
        """Test retrieving task with nonexistent but valid ID."""
        nonexistent_id = str(ObjectId())
        result = await task_repository.get_task_by_id(nonexistent_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_user(self, task_repository, creator_id, assignee_id):
        """Test retrieving tasks by user (creator or assignee)."""
        # Create tasks where user is creator
        task_data_1 = TaskCreate(
            title="Creator Task 1",
            description="Task created by user",
            due_date=datetime.now() + timedelta(days=1)
        )
        created_task_1 = await task_repository.create_task(task_data_1, creator_id)
        
        # Create task where user is assignee
        task_data_2 = TaskCreate(
            title="Assignee Task",
            description="Task assigned to user",
            due_date=datetime.now() + timedelta(days=2),
            assignee_id=creator_id
        )
        await task_repository.create_task(task_data_2, assignee_id)
        
        # Get tasks for the user
        user_tasks = await task_repository.get_tasks_by_user(creator_id)
        
        assert len(user_tasks) == 2
        task_titles = [task.title for task in user_tasks]
        assert "Creator Task 1" in task_titles
        assert "Assignee Task" in task_titles
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_creator(self, task_repository, creator_id, assignee_id):
        """Test retrieving tasks by creator."""
        # Create tasks by creator
        task_data_1 = TaskCreate(
            title="Creator Task 1",
            description="First task by creator",
            due_date=datetime.now() + timedelta(days=1)
        )
        task_data_2 = TaskCreate(
            title="Creator Task 2",
            description="Second task by creator",
            due_date=datetime.now() + timedelta(days=2)
        )
        
        await task_repository.create_task(task_data_1, creator_id)
        await task_repository.create_task(task_data_2, creator_id)
        
        # Create task by different user
        task_data_3 = TaskCreate(
            title="Other User Task",
            description="Task by other user",
            due_date=datetime.now() + timedelta(days=3)
        )
        await task_repository.create_task(task_data_3, assignee_id)
        
        # Get tasks by creator
        creator_tasks = await task_repository.get_tasks_by_creator(creator_id)
        
        assert len(creator_tasks) == 2
        for task in creator_tasks:
            assert task.creator_id == creator_id
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_assignee(self, task_repository, creator_id, assignee_id):
        """Test retrieving tasks by assignee."""
        # Create tasks assigned to user
        task_data_1 = TaskCreate(
            title="Assigned Task 1",
            description="First assigned task",
            due_date=datetime.now() + timedelta(days=1),
            assignee_id=assignee_id
        )
        task_data_2 = TaskCreate(
            title="Assigned Task 2",
            description="Second assigned task",
            due_date=datetime.now() + timedelta(days=2),
            assignee_id=assignee_id
        )
        
        await task_repository.create_task(task_data_1, creator_id)
        await task_repository.create_task(task_data_2, creator_id)
        
        # Create unassigned task
        task_data_3 = TaskCreate(
            title="Unassigned Task",
            description="Task without assignee",
            due_date=datetime.now() + timedelta(days=3)
        )
        await task_repository.create_task(task_data_3, creator_id)
        
        # Get tasks by assignee
        assigned_tasks = await task_repository.get_tasks_by_assignee(assignee_id)
        
        assert len(assigned_tasks) == 2
        for task in assigned_tasks:
            assert task.assignee_id == assignee_id
    
    @pytest.mark.asyncio
    async def test_update_task_by_creator(self, task_repository, sample_task_data, creator_id):
        """Test updating task by creator."""
        # Create task
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        # Update task
        update_data = TaskUpdate(
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS
        )
        
        updated_task = await task_repository.update_task(str(created_task.id), update_data, creator_id)
        
        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.description == sample_task_data.description  # Unchanged
        assert updated_task.updated_at > created_task.updated_at
    
    @pytest.mark.asyncio
    async def test_update_task_by_assignee(self, task_repository, creator_id, assignee_id):
        """Test updating task by assignee."""
        # Create task with assignee
        task_data = TaskCreate(
            title="Assigned Task",
            description="Task for assignee to update",
            due_date=datetime.now() + timedelta(days=1),
            assignee_id=assignee_id
        )
        created_task = await task_repository.create_task(task_data, creator_id)
        
        # Update task as assignee
        update_data = TaskUpdate(status=TaskStatus.DONE)
        updated_task = await task_repository.update_task(str(created_task.id), update_data, assignee_id)
        
        assert updated_task is not None
        assert updated_task.status == TaskStatus.DONE
    
    @pytest.mark.asyncio
    async def test_update_task_unauthorized(self, task_repository, sample_task_data, creator_id):
        """Test updating task by unauthorized user."""
        # Create task
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        # Try to update as unauthorized user
        update_data = TaskUpdate(title="Unauthorized Update")
        unauthorized_user_id = 999
        
        with pytest.raises(PermissionError, match="User does not have permission"):
            await task_repository.update_task(str(created_task.id), update_data, unauthorized_user_id)
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, task_repository):
        """Test updating nonexistent task."""
        nonexistent_id = str(ObjectId())
        update_data = TaskUpdate(title="Update")
        
        result = await task_repository.update_task(nonexistent_id, update_data, 1)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_task_by_creator(self, task_repository, sample_task_data, creator_id):
        """Test deleting task by creator."""
        # Create task
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        # Delete task
        result = await task_repository.delete_task(str(created_task.id), creator_id)
        assert result is True
        
        # Verify task is deleted
        deleted_task = await task_repository.get_task_by_id(str(created_task.id))
        assert deleted_task is None
    
    @pytest.mark.asyncio
    async def test_delete_task_by_non_creator(self, task_repository, sample_task_data, creator_id, assignee_id):
        """Test deleting task by non-creator (should fail)."""
        # Create task
        created_task = await task_repository.create_task(sample_task_data, creator_id)
        
        # Try to delete as non-creator
        with pytest.raises(PermissionError, match="Only task creator can delete"):
            await task_repository.delete_task(str(created_task.id), assignee_id)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(self, task_repository):
        """Test deleting nonexistent task."""
        nonexistent_id = str(ObjectId())
        result = await task_repository.delete_task(nonexistent_id, 1)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, task_repository, creator_id):
        """Test retrieving tasks by status."""
        # Create tasks with different statuses
        task_data_1 = TaskCreate(
            title="Todo Task",
            description="Task in todo status",
            due_date=datetime.now() + timedelta(days=1),
            status=TaskStatus.TO_DO
        )
        task_data_2 = TaskCreate(
            title="In Progress Task",
            description="Task in progress",
            due_date=datetime.now() + timedelta(days=2),
            status=TaskStatus.IN_PROGRESS
        )
        
        await task_repository.create_task(task_data_1, creator_id)
        await task_repository.create_task(task_data_2, creator_id)
        
        # Get tasks by status
        todo_tasks = await task_repository.get_tasks_by_status(TaskStatus.TO_DO, creator_id)
        progress_tasks = await task_repository.get_tasks_by_status(TaskStatus.IN_PROGRESS, creator_id)
        
        assert len(todo_tasks) == 1
        assert len(progress_tasks) == 1
        assert todo_tasks[0].status == TaskStatus.TO_DO
        assert progress_tasks[0].status == TaskStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_count_user_tasks(self, task_repository, creator_id, assignee_id):
        """Test counting user tasks."""
        # Create tasks for user
        task_data_1 = TaskCreate(
            title="Creator Task",
            description="Task created by user",
            due_date=datetime.now() + timedelta(days=1)
        )
        task_data_2 = TaskCreate(
            title="Assigned Task",
            description="Task assigned to user",
            due_date=datetime.now() + timedelta(days=2),
            assignee_id=creator_id
        )
        
        await task_repository.create_task(task_data_1, creator_id)
        await task_repository.create_task(task_data_2, assignee_id)
        
        # Count tasks
        count = await task_repository.count_user_tasks(creator_id)
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_pagination(self, task_repository, creator_id):
        """Test pagination in task retrieval."""
        # Create multiple tasks
        for i in range(5):
            task_data = TaskCreate(
                title=f"Task {i}",
                description=f"Description {i}",
                due_date=datetime.now() + timedelta(days=i+1)
            )
            await task_repository.create_task(task_data, creator_id)
        
        # Test pagination
        first_page = await task_repository.get_tasks_by_user(creator_id, skip=0, limit=2)
        second_page = await task_repository.get_tasks_by_user(creator_id, skip=2, limit=2)
        
        assert len(first_page) == 2
        assert len(second_page) == 2
        
        # Ensure different tasks
        first_page_ids = [str(task.id) for task in first_page]
        second_page_ids = [str(task.id) for task in second_page]
        assert len(set(first_page_ids) & set(second_page_ids)) == 0