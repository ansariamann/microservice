"""
Tests for Task Service data models and validation.
"""

import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from pydantic import ValidationError

from app.models import (
    TaskStatus, TaskBase, TaskCreate, TaskUpdate, Task, TaskResponse,
    PyObjectId, task_helper
)


class TestTaskStatus:
    """Test TaskStatus enumeration."""
    
    def test_task_status_values(self):
        """Test that TaskStatus has correct values."""
        assert TaskStatus.TO_DO == "to_do"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.DONE == "done"


class TestPyObjectId:
    """Test PyObjectId custom type."""
    
    def test_valid_object_id(self):
        """Test validation of valid ObjectId."""
        valid_id = ObjectId()
        result = PyObjectId.validate(str(valid_id))
        assert isinstance(result, ObjectId)
        assert result == valid_id
    
    def test_invalid_object_id(self):
        """Test validation of invalid ObjectId."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")


class TestTaskBase:
    """Test TaskBase model validation."""
    
    def test_valid_task_base(self):
        """Test creating valid TaskBase instance."""
        due_date = datetime.now() + timedelta(days=1)
        task = TaskBase(
            title="Test Task",
            description="Test description",
            due_date=due_date,
            status=TaskStatus.TO_DO,
            assignee_id=1
        )
        
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.due_date == due_date
        assert task.status == TaskStatus.TO_DO
        assert task.assignee_id == 1
    
    def test_empty_title_validation(self):
        """Test that empty title raises validation error."""
        due_date = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            TaskBase(
                title="",
                description="Test description",
                due_date=due_date
            )
    
    def test_whitespace_title_validation(self):
        """Test that whitespace-only title raises validation error."""
        due_date = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            TaskBase(
                title="   ",
                description="Test description",
                due_date=due_date
            )
    
    def test_title_trimming(self):
        """Test that title is trimmed of whitespace."""
        due_date = datetime.now() + timedelta(days=1)
        task = TaskBase(
            title="  Test Task  ",
            description="Test description",
            due_date=due_date
        )
        
        assert task.title == "Test Task"
    
    def test_description_trimming(self):
        """Test that description is trimmed of whitespace."""
        due_date = datetime.now() + timedelta(days=1)
        task = TaskBase(
            title="Test Task",
            description="  Test description  ",
            due_date=due_date
        )
        
        assert task.description == "Test description"
    
    def test_past_due_date_validation(self):
        """Test that past due date raises validation error."""
        past_date = datetime.now() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            TaskBase(
                title="Test Task",
                description="Test description",
                due_date=past_date
            )
    
    def test_default_status(self):
        """Test that default status is TO_DO."""
        due_date = datetime.now() + timedelta(days=1)
        task = TaskBase(
            title="Test Task",
            description="Test description",
            due_date=due_date
        )
        
        assert task.status == TaskStatus.TO_DO
    
    def test_optional_assignee(self):
        """Test that assignee_id is optional."""
        due_date = datetime.now() + timedelta(days=1)
        task = TaskBase(
            title="Test Task",
            description="Test description",
            due_date=due_date
        )
        
        assert task.assignee_id is None


class TestTaskCreate:
    """Test TaskCreate model."""
    
    def test_task_create_inherits_validation(self):
        """Test that TaskCreate inherits validation from TaskBase."""
        due_date = datetime.now() + timedelta(days=1)
        
        with pytest.raises(ValidationError):
            TaskCreate(
                title="",
                description="Test description",
                due_date=due_date
            )


class TestTaskUpdate:
    """Test TaskUpdate model validation."""
    
    def test_all_fields_optional(self):
        """Test that all fields in TaskUpdate are optional."""
        task_update = TaskUpdate()
        
        assert task_update.title is None
        assert task_update.description is None
        assert task_update.due_date is None
        assert task_update.status is None
        assert task_update.assignee_id is None
    
    def test_partial_update(self):
        """Test partial update with some fields."""
        task_update = TaskUpdate(
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS
        )
        
        assert task_update.title == "Updated Title"
        assert task_update.status == TaskStatus.IN_PROGRESS
        assert task_update.description is None
    
    def test_title_validation_when_provided(self):
        """Test title validation when title is provided."""
        with pytest.raises(ValidationError):
            TaskUpdate(title="")
    
    def test_due_date_validation_when_provided(self):
        """Test due date validation when due date is provided."""
        past_date = datetime.now() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Due date cannot be in the past"):
            TaskUpdate(due_date=past_date)
    
    def test_title_trimming_when_provided(self):
        """Test title trimming when title is provided."""
        task_update = TaskUpdate(title="  Updated Title  ")
        assert task_update.title == "Updated Title"


class TestTask:
    """Test complete Task model."""
    
    def test_task_with_all_fields(self):
        """Test creating Task with all fields."""
        due_date = datetime.now() + timedelta(days=1)
        created_at = datetime.now()
        
        task = Task(
            title="Test Task",
            description="Test description",
            due_date=due_date,
            status=TaskStatus.TO_DO,
            creator_id=1,
            assignee_id=2,
            created_at=created_at,
            updated_at=created_at
        )
        
        assert task.title == "Test Task"
        assert task.creator_id == 1
        assert task.assignee_id == 2
        assert task.created_at == created_at
        assert isinstance(task.id, PyObjectId)
    
    def test_task_default_timestamps(self):
        """Test that Task has default timestamps."""
        due_date = datetime.now() + timedelta(days=1)
        
        task = Task(
            title="Test Task",
            description="Test description",
            due_date=due_date,
            creator_id=1
        )
        
        assert task.created_at is not None
        assert task.updated_at is not None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)


class TestTaskHelper:
    """Test task_helper utility function."""
    
    def test_task_helper_conversion(self):
        """Test converting MongoDB document to dictionary."""
        object_id = ObjectId()
        due_date = datetime.now() + timedelta(days=1)
        created_at = datetime.now()
        
        mongo_doc = {
            "_id": object_id,
            "title": "Test Task",
            "description": "Test description",
            "due_date": due_date,
            "status": "to_do",
            "creator_id": 1,
            "assignee_id": 2,
            "created_at": created_at,
            "updated_at": created_at
        }
        
        result = task_helper(mongo_doc)
        
        assert result["id"] == str(object_id)
        assert result["title"] == "Test Task"
        assert result["description"] == "Test description"
        assert result["due_date"] == due_date
        assert result["status"] == "to_do"
        assert result["creator_id"] == 1
        assert result["assignee_id"] == 2
        assert result["created_at"] == created_at
        assert result["updated_at"] == created_at
    
    def test_task_helper_without_assignee(self):
        """Test task_helper with no assignee."""
        object_id = ObjectId()
        due_date = datetime.now() + timedelta(days=1)
        created_at = datetime.now()
        
        mongo_doc = {
            "_id": object_id,
            "title": "Test Task",
            "description": "Test description",
            "due_date": due_date,
            "status": "to_do",
            "creator_id": 1,
            "created_at": created_at,
            "updated_at": created_at
        }
        
        result = task_helper(mongo_doc)
        
        assert result["assignee_id"] is None