# Task Service API Documentation

## Overview

The Task Service provides task management functionality for the distributed task management system. It handles task creation, updates, assignments, status management, and authorization with JWT-based authentication.

**Base URL**: `http://localhost:8002`  
**API Version**: v1  
**Authentication**: JWT Bearer Token (except for health checks)

## Authentication

### JWT Token Format

All authenticated endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <jwt-token>
```

**Token Structure**:

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "exp": 1640995200,
  "iat": 1640908800
}
```

**Token Expiration**: 24 hours

## Task Status Values

Tasks can have one of the following status values:

- `to_do`: Task is created but not started
- `in_progress`: Task is being worked on
- `done`: Task is completed

## API Endpoints

### 1. Create Task

Create a new task.

**Endpoint**: `POST /api/v1/tasks`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

#### Request Body

```json
{
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "to_do",
  "assignee_id": 2
}
```

#### Request Schema

| Field       | Type     | Required | Validation                       | Description                  |
| ----------- | -------- | -------- | -------------------------------- | ---------------------------- |
| title       | string   | Yes      | 1-200 characters, non-empty      | Task title                   |
| description | string   | Yes      | Max 2000 characters              | Task description             |
| due_date    | datetime | Yes      | Must be in the future            | Task due date (ISO 8601)     |
| status      | string   | No       | One of: to_do, in_progress, done | Task status (default: to_do) |
| assignee_id | integer  | No       | Valid user ID                    | ID of assigned user          |

#### Response (201 Created)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "to_do",
  "creator_id": 1,
  "assignee_id": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### Error Responses

**400 Bad Request** - Validation error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Due date cannot be in the past",
    "details": {
      "field": "due_date"
    }
  }
}
```

**401 Unauthorized** - Missing or invalid token:

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired token"
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8002/api/v1/tasks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the task management system",
    "due_date": "2024-12-31T23:59:59",
    "assignee_id": 2
  }'
```

### 2. Get User Tasks

Retrieve tasks for the authenticated user (created by or assigned to).

**Endpoint**: `GET /api/v1/tasks`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters

| Parameter     | Type   | Required | Default | Description                                 |
| ------------- | ------ | -------- | ------- | ------------------------------------------- |
| skip          | int    | No       | 0       | Number of tasks to skip (pagination)        |
| limit         | int    | No       | 100     | Maximum tasks to return (1-1000)            |
| status_filter | string | No       | None    | Filter by status (to_do, in_progress, done) |

#### Response (200 OK)

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the task management system",
    "due_date": "2024-12-31T23:59:59",
    "status": "to_do",
    "creator_id": 1,
    "assignee_id": 2,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### cURL Example

```bash
curl -X GET "http://localhost:8002/api/v1/tasks?limit=10&status_filter=to_do" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Get Specific Task

Retrieve a specific task by ID.

**Endpoint**: `GET /api/v1/tasks/{task_id}`  
**Authentication**: JWT Bearer Token required

#### Path Parameters

| Parameter | Type   | Required | Description |
| --------- | ------ | -------- | ----------- |
| task_id   | string | Yes      | Task ID     |

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "to_do",
  "creator_id": 1,
  "assignee_id": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

#### Error Responses

**403 Forbidden** - Access denied:

```json
{
  "error": {
    "code": "ACCESS_DENIED",
    "message": "Access denied to this task"
  }
}
```

**404 Not Found** - Task not found:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found"
  }
}
```

#### cURL Example

```bash
curl -X GET http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Update Task

Update an existing task.

**Endpoint**: `PUT /api/v1/tasks/{task_id}`  
**Authentication**: JWT Bearer Token required

#### Request Body

```json
{
  "title": "Updated task title",
  "description": "Updated description",
  "due_date": "2024-12-31T23:59:59",
  "status": "in_progress",
  "assignee_id": 3
}
```

#### Request Schema

All fields are optional for updates:

| Field       | Type     | Required | Validation                       | Description         |
| ----------- | -------- | -------- | -------------------------------- | ------------------- |
| title       | string   | No       | 1-200 characters if provided     | Task title          |
| description | string   | No       | Max 2000 characters              | Task description    |
| due_date    | datetime | No       | Must be in the future            | Task due date       |
| status      | string   | No       | One of: to_do, in_progress, done | Task status         |
| assignee_id | integer  | No       | Valid user ID                    | ID of assigned user |

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Updated task title",
  "description": "Updated description",
  "due_date": "2024-12-31T23:59:59",
  "status": "in_progress",
  "creator_id": 1,
  "assignee_id": 3,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:45:00"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated task title",
    "status": "in_progress"
  }'
```

### 5. Delete Task

Delete a task (only task creator can delete).

**Endpoint**: `DELETE /api/v1/tasks/{task_id}`  
**Authentication**: JWT Bearer Token required

#### Response (204 No Content)

No response body.

#### Error Responses

**403 Forbidden** - Permission denied:

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Permission denied to delete this task"
  }
}
```

#### cURL Example

```bash
curl -X DELETE http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 6. Get Task Count

Get total task count for the authenticated user.

**Endpoint**: `GET /api/v1/tasks/count`  
**Authentication**: JWT Bearer Token required

#### Response (200 OK)

```json
{
  "count": 15
}
```

#### cURL Example

```bash
curl -X GET http://localhost:8002/api/v1/tasks/count \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 7. Assign Task

Assign a task to a user.

**Endpoint**: `PUT /api/v1/tasks/{task_id}/assign`  
**Authentication**: JWT Bearer Token required

#### Request Body

```json
{
  "assignee_id": 2
}
```

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "to_do",
  "creator_id": 1,
  "assignee_id": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:45:00"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011/assign \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"assignee_id": 2}'
```

### 8. Unassign Task

Remove assignment from a task.

**Endpoint**: `PUT /api/v1/tasks/{task_id}/unassign`  
**Authentication**: JWT Bearer Token required

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "to_do",
  "creator_id": 1,
  "assignee_id": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:45:00"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011/unassign \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 9. Change Task Status

Update task status.

**Endpoint**: `PUT /api/v1/tasks/{task_id}/status`  
**Authentication**: JWT Bearer Token required

#### Request Body

```json
{
  "status": "in_progress"
}
```

#### Request Schema

| Field  | Type   | Required | Validation                       | Description |
| ------ | ------ | -------- | -------------------------------- | ----------- |
| status | string | Yes      | One of: to_do, in_progress, done | New status  |

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "Complete project documentation",
  "description": "Write comprehensive documentation for the task management system",
  "due_date": "2024-12-31T23:59:59",
  "status": "in_progress",
  "creator_id": 1,
  "assignee_id": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T14:45:00"
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8002/api/v1/tasks/507f1f77bcf86cd799439011/status \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### 10. Get Assigned Tasks

Get tasks assigned to the authenticated user.

**Endpoint**: `GET /api/v1/tasks/assigned`  
**Authentication**: JWT Bearer Token required

#### Query Parameters

| Parameter | Type | Required | Default | Description                          |
| --------- | ---- | -------- | ------- | ------------------------------------ |
| skip      | int  | No       | 0       | Number of tasks to skip (pagination) |
| limit     | int  | No       | 100     | Maximum tasks to return (1-1000)     |

#### Response (200 OK)

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the task management system",
    "due_date": "2024-12-31T23:59:59",
    "status": "to_do",
    "creator_id": 1,
    "assignee_id": 2,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### cURL Example

```bash
curl -X GET "http://localhost:8002/api/v1/tasks/assigned?limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 11. Get Created Tasks

Get tasks created by the authenticated user.

**Endpoint**: `GET /api/v1/tasks/created`  
**Authentication**: JWT Bearer Token required

#### Query Parameters

| Parameter | Type | Required | Default | Description                          |
| --------- | ---- | -------- | ------- | ------------------------------------ |
| skip      | int  | No       | 0       | Number of tasks to skip (pagination) |
| limit     | int  | No       | 100     | Maximum tasks to return (1-1000)     |

#### Response (200 OK)

```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "title": "Complete project documentation",
    "description": "Write comprehensive documentation for the task management system",
    "due_date": "2024-12-31T23:59:59",
    "status": "to_do",
    "creator_id": 1,
    "assignee_id": 2,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

#### cURL Example

```bash
curl -X GET "http://localhost:8002/api/v1/tasks/created?limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Health Check Endpoints

### Comprehensive Health Check

**Endpoint**: `GET /health`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "task-service",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 25
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 45.2
    },
    "disk": {
      "status": "healthy",
      "usage_percent": 67.8
    },
    "notification_service": {
      "status": "healthy",
      "response_time_ms": 150
    }
  }
}
```

### Simple Health Check

**Endpoint**: `GET /health/simple`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "status": "healthy",
  "service": "task-service",
  "version": "1.0.0"
}
```

## Metrics Endpoint

**Endpoint**: `GET /metrics`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "task-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "request_count": 2500,
  "error_count": 45,
  "average_response_time_ms": 185.3,
  "uptime_seconds": 86400
}
```

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_name",
      "reason": "specific validation error"
    }
  }
}
```

### Common Error Codes

| Code                 | HTTP Status | Description                  |
| -------------------- | ----------- | ---------------------------- |
| VALIDATION_ERROR     | 400         | Request validation failed    |
| AUTHENTICATION_ERROR | 401         | Invalid credentials or token |
| ACCESS_DENIED        | 403         | Insufficient permissions     |
| NOT_FOUND            | 404         | Resource not found           |
| PERMISSION_DENIED    | 403         | Operation not allowed        |
| INTERNAL_ERROR       | 500         | Internal server error        |

## Rate Limiting

The Task Service implements rate limiting:

- **Limit**: 200 requests per minute per IP
- **Response Header**: `X-RateLimit-Remaining`
- **Error Response** (429 Too Many Requests):

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later."
  }
}
```

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8002/docs`
- **ReDoc**: `http://localhost:8002/redoc`
- **OpenAPI JSON**: `http://localhost:8002/openapi.json`

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require("axios");

class TaskServiceClient {
  constructor(baseURL = "http://localhost:8002") {
    this.client = axios.create({ baseURL });
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async createTask(taskData) {
    const response = await this.client.post("/api/v1/tasks", taskData, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return response.data;
  }

  async getTasks(options = {}) {
    const { skip = 0, limit = 100, status_filter } = options;
    const params = { skip, limit };
    if (status_filter) params.status_filter = status_filter;

    const response = await this.client.get("/api/v1/tasks", {
      headers: { Authorization: `Bearer ${this.token}` },
      params,
    });
    return response.data;
  }

  async getTask(taskId) {
    const response = await this.client.get(`/api/v1/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return response.data;
  }

  async updateTask(taskId, updates) {
    const response = await this.client.put(`/api/v1/tasks/${taskId}`, updates, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return response.data;
  }

  async deleteTask(taskId) {
    await this.client.delete(`/api/v1/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
  }

  async assignTask(taskId, assigneeId) {
    const response = await this.client.put(
      `/api/v1/tasks/${taskId}/assign`,
      { assignee_id: assigneeId },
      {
        headers: { Authorization: `Bearer ${this.token}` },
      }
    );
    return response.data;
  }

  async changeTaskStatus(taskId, status) {
    const response = await this.client.put(
      `/api/v1/tasks/${taskId}/status`,
      { status },
      {
        headers: { Authorization: `Bearer ${this.token}` },
      }
    );
    return response.data;
  }
}
```

### Python

```python
import requests
from typing import Optional, Dict, Any, List

class TaskServiceClient:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def set_token(self, token: str):
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/tasks",
            json=task_data,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"skip": skip, "limit": limit}
        if status_filter:
            params["status_filter"] = status_filter

        response = requests.get(
            f"{self.base_url}/api/v1/tasks",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_task(self, task_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            json=updates,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def delete_task(self, task_id: str) -> None:
        response = requests.delete(
            f"{self.base_url}/api/v1/tasks/{task_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()

    def assign_task(self, task_id: str, assignee_id: int) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}/api/v1/tasks/{task_id}/assign",
            json={"assignee_id": assignee_id},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def change_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}/api/v1/tasks/{task_id}/status",
            json={"status": status},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
```
