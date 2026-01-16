"""
Integration tests for Task Service workflows.
Tests complete task management workflows end-to-end.
"""

import pytest
import pytest_asyncio
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.auth import auth_settings


class TestTaskWorkflowIntegration:
    """Test complete task management workflows."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_token(self):
        """Create valid JWT token for user 1."""
        payload = {
            "user_id": 1,
            "email": "creator@example.com",
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now().timestamp())
        }
        return jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
    
    @pytest.fixture
    def assignee_token(self):
        """Create valid JWT token for user 2 (assignee)."""
        payload = {
            "user_id": 2,
            "email": "assignee@example.com",
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now().timestamp())
        }
        return jwt.encode(payload, auth_settings.jwt_secret, algorithm=auth_settings.jwt_algorithm)
    
    @pytest.fixture
    def auth_headers(self, valid_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {valid_token}"}
    
    @pytest.fixture
    def assignee_headers(self, assignee_token):
        """Create authorization headers for assignee."""
        return {"Authorization": f"Bearer {assignee_token}"}
    
    @pytest.fixture
    def sample_task_data(self):
        """Sample task creation data."""
        return {
            "title": "Integration Test Task",
            "description": "Task for integration testing",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "to_do"
        }
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "task-service"}
    
    @patch('app.database.db_manager')
    @patch('app.services.TaskService')
    def test_complete_task_workflow(self, mock_service_class, mock_db_manager, client, auth_headers, assignee_headers, sample_task_data):
        """Test complete task workflow from creation to completion."""
        # Mock the database manager
        mock_db_manager.get_database.return_value = AsyncMock()
        
        # Mock task service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        # Mock task creation
        created_task = {
            "id": "507f1f77bcf86cd799439011",
            "title": sample_task_data["title"],
            "description": sample_task_data["description"],
            "due_date": sample_task_data["due_date"],
            "status": "to_do",
            "creator_id": 1,
            "assignee_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_service.create_task.return_value = type('TaskResponse', (), created_task)()
        
        # Step 1: Create task
        response = client.post("/api/v1/tasks", json=sample_task_data, headers=auth_headers)
        assert response.status_code == 201
        task_data = response.json()
        task_id = task_data["id"]
        assert task_data["title"] == sample_task_data["title"]
        assert task_data["status"] == "to_do"
        assert task_data["creator_id"] == 1
        assert task_data["assignee_id"] is None
        
        # Mock task assignment
        assigned_task = created_task.copy()
        assigned_task["assignee_id"] = 2
        mock_service.assign_task.return_value = type('TaskResponse', (), assigned_task)()
        
        # Step 2: Assign task
        response = client.put(
            f"/api/v1/tasks/{task_id}/assign",
            json={"assignee_id": 2},
            headers=auth_headers
        )
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["assignee_id"] == 2
        
        # Mock status change
        in_progress_task = assigned_task.copy()
        in_progress_task["status"] = "in_progress"
        mock_service.change_task_status.return_value = type('TaskResponse', (), in_progress_task)()
        
        # Step 3: Start work (change status to in_progress)
        response = client.put(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress"},
            headers=assignee_headers
        )
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "in_progress"
        
        # Mock task completion
        completed_task = in_progress_task.copy()
        completed_task["status"] = "done"
        mock_service.change_task_status.return_value = type('TaskResponse', (), completed_task)()
        
        # Step 4: Complete task
        response = client.put(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "done"},
            headers=assignee_headers
        )
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "done"
        
        # Mock task retrieval
        mock_service.get_task_by_id.return_value = type('TaskResponse', (), completed_task)()
        
        # Step 5: Verify final state
        response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "done"
        assert task_data["assignee_id"] == 2
    
    @patch('app.database.db_manager')
    @patch('app.services.TaskService')
    def test_task_list_filtering(self, mock_service_class, mock_db_manager, client, auth_headers, sample_task_data):
        """Test task list filtering functionality."""
        # Mock the database manager
        mock_db_manager.get_database.return_value = AsyncMock()
        
        # Mock task service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        # Mock tasks with different statuses
        todo_task = {
            "id": "507f1f77bcf86cd799439011",
            "title": "Todo Task",
            "description": "Task in todo status",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "to_do",
            "creator_id": 1,
            "assignee_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        done_task = {
            "id": "507f1f77bcf86cd799439012",
            "title": "Done Task",
            "description": "Task in done status",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "done",
            "creator_id": 1,
            "assignee_id": 2,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock service responses
        mock_service.get_user_tasks.return_value = [
            type('TaskResponse', (), todo_task)(),
            type('TaskResponse', (), done_task)()
        ]
        mock_service.get_tasks_by_status.return_value = [
            type('TaskResponse', (), todo_task)()
        ]
        
        # Test getting all tasks
        response = client.get("/api/v1/tasks", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        
        # Test filtering by status
        response = client.get("/api/v1/tasks?status_filter=to_do", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["status"] == "to_do"
    
    @patch('app.database.db_manager')
    @patch('app.services.TaskService')
    def test_task_assignment_workflow(self, mock_service_class, mock_db_manager, client, auth_headers, assignee_headers):
        """Test task assignment and unassignment workflow."""
        # Mock the database manager
        mock_db_manager.get_database.return_value = AsyncMock()
        
        # Mock task service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        task_id = "507f1f77bcf86cd799439011"
        
        # Mock unassigned task
        unassigned_task = {
            "id": task_id,
            "title": "Assignment Test Task",
            "description": "Task for assignment testing",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "to_do",
            "creator_id": 1,
            "assignee_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock assigned task
        assigned_task = unassigned_task.copy()
        assigned_task["assignee_id"] = 2
        
        # Test assignment
        mock_service.assign_task.return_value = type('TaskResponse', (), assigned_task)()
        response = client.put(
            f"/api/v1/tasks/{task_id}/assign",
            json={"assignee_id": 2},
            headers=auth_headers
        )
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["assignee_id"] == 2
        
        # Test unassignment
        mock_service.unassign_task.return_value = type('TaskResponse', (), unassigned_task)()
        response = client.put(f"/api/v1/tasks/{task_id}/unassign", headers=auth_headers)
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["assignee_id"] is None
    
    def test_authentication_required(self, client, sample_task_data):
        """Test that authentication is required for protected endpoints."""
        # Test without authorization header
        response = client.post("/api/v1/tasks", json=sample_task_data)
        assert response.status_code == 401
        
        response = client.get("/api/v1/tasks")
        assert response.status_code == 401
        
        response = client.get("/api/v1/tasks/some-id")
        assert response.status_code == 401
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid.token"}
        response = client.post("/api/v1/tasks", json=sample_task_data, headers=invalid_headers)
        assert response.status_code == 401
    
    @patch('app.database.db_manager')
    @patch('app.services.TaskService')
    def test_error_handling(self, mock_service_class, mock_db_manager, client, auth_headers):
        """Test error handling in API endpoints."""
        # Mock the database manager
        mock_db_manager.get_database.return_value = AsyncMock()
        
        # Mock task service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        # Test 404 error
        mock_service.get_task_by_id.return_value = None
        response = client.get("/api/v1/tasks/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Test permission error
        mock_service.get_task_by_id.side_effect = PermissionError("Access denied")
        response = client.get("/api/v1/tasks/forbidden-task", headers=auth_headers)
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
        
        # Test validation error
        invalid_task_data = {
            "title": "",  # Invalid empty title
            "description": "Test description",
            "due_date": "invalid-date-format"
        }
        response = client.post("/api/v1/tasks", json=invalid_task_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    @patch('app.database.db_manager')
    @patch('app.services.TaskService')
    def test_pagination(self, mock_service_class, mock_db_manager, client, auth_headers):
        """Test pagination in task listing."""
        # Mock the database manager
        mock_db_manager.get_database.return_value = AsyncMock()
        
        # Mock task service
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        
        # Mock paginated response
        mock_tasks = []
        for i in range(5):
            task = {
                "id": f"507f1f77bcf86cd79943901{i}",
                "title": f"Task {i}",
                "description": f"Description {i}",
                "due_date": (datetime.now() + timedelta(days=i+1)).isoformat(),
                "status": "to_do",
                "creator_id": 1,
                "assignee_id": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_tasks.append(type('TaskResponse', (), task)())
        
        # Mock first page (limit 3)
        mock_service.get_user_tasks.return_value = mock_tasks[:3]
        response = client.get("/api/v1/tasks?limit=3", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3
        
        # Mock second page (skip 3, limit 3)
        mock_service.get_user_tasks.return_value = mock_tasks[3:]
        response = client.get("/api/v1/tasks?skip=3&limit=3", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2  # Only 2 remaining tasks


class TestTaskServiceDocumentation:
    """Test API documentation and OpenAPI schema."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["info"]["title"] == "Task Service"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "components" in schema
    
    def test_docs_endpoint_available(self, client):
        """Test that Swagger docs endpoint is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc endpoint is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_api_endpoints_documented(self, client):
        """Test that all API endpoints are documented in OpenAPI schema."""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]
        
        # Check that main endpoints are documented
        expected_paths = [
            "/health",
            "/api/v1/tasks",
            "/api/v1/tasks/{task_id}",
            "/api/v1/tasks/{task_id}/assign",
            "/api/v1/tasks/{task_id}/unassign",
            "/api/v1/tasks/{task_id}/status",
            "/api/v1/tasks/assigned",
            "/api/v1/tasks/created",
            "/api/v1/tasks/count"
        ]
        
        for path in expected_paths:
            assert path in paths, f"Path {path} not found in OpenAPI schema"
    
    def test_response_models_documented(self, client):
        """Test that response models are properly documented."""
        response = client.get("/openapi.json")
        schema = response.json()
        components = schema["components"]["schemas"]
        
        # Check that main models are documented
        expected_models = ["TaskResponse", "TaskCreate", "TaskUpdate"]
        
        for model in expected_models:
            assert model in components, f"Model {model} not found in OpenAPI schema"
        
        # Check TaskResponse model structure
        task_response = components["TaskResponse"]
        required_fields = ["id", "title", "description", "due_date", "status", "creator_id", "created_at", "updated_at"]
        
        for field in required_fields:
            assert field in task_response["properties"], f"Field {field} not found in TaskResponse model"