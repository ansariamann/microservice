# Notification Service API Documentation

## Overview

The Notification Service manages task-related notifications in the distributed task management system. It provides endpoints for creating notifications (internal service calls) and retrieving user notifications with JWT-based authentication.

**Base URL**: `http://localhost:8003`  
**API Version**: v1  
**Authentication**: JWT Bearer Token (except for internal endpoints and health checks)

## Authentication

### JWT Token Format

Authenticated endpoints require a JWT token in the Authorization header:

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

## Notification Types

The service supports the following notification types:

- `task_assigned`: When a task is assigned to a user
- `task_updated`: When a task status is updated

## API Endpoints

### 1. Create Notification (Internal)

Create a new notification. This endpoint is used by other services (like Task Service) for internal communication.

**Endpoint**: `POST /api/v1/notifications`  
**Authentication**: None required (internal service endpoint)

#### Request Headers

```http
Content-Type: application/json
```

#### Request Body

```json
{
  "user_id": 2,
  "task_id": "507f1f77bcf86cd799439011",
  "message": "You have been assigned to task 'Complete project documentation' by John Doe",
  "type": "task_assigned"
}
```

#### Request Schema

| Field   | Type   | Required | Validation                          | Description                  |
| ------- | ------ | -------- | ----------------------------------- | ---------------------------- |
| user_id | int    | Yes      | Must be > 0                         | ID of user to notify         |
| task_id | string | Yes      | Non-empty string                    | ID of related task           |
| message | string | Yes      | 1-500 characters                    | Notification message content |
| type    | string | Yes      | One of: task_assigned, task_updated | Type of notification         |

#### Response (201 Created)

```json
{
  "id": 1,
  "user_id": 2,
  "task_id": "507f1f77bcf86cd799439011",
  "message": "You have been assigned to task 'Complete project documentation' by John Doe",
  "type": "task_assigned",
  "is_read": false,
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

#### Error Responses

**400 Bad Request** - Validation error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Type must be one of: ['task_assigned', 'task_updated']",
    "details": {
      "field": "type"
    }
  }
}
```

**500 Internal Server Error** - Creation failed:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Failed to create notification"
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8003/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "task_id": "507f1f77bcf86cd799439011",
    "message": "You have been assigned to task '\''Complete project documentation'\'' by John Doe",
    "type": "task_assigned"
  }'
```

### 2. Get User Notifications

Retrieve notifications for the authenticated user.

**Endpoint**: `GET /api/v1/notifications`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Query Parameters

| Parameter   | Type | Required | Default | Description                               |
| ----------- | ---- | -------- | ------- | ----------------------------------------- |
| unread_only | bool | No       | false   | If true, only return unread notifications |
| limit       | int  | No       | 50      | Maximum notifications to return (1-100)   |

#### Response (200 OK)

```json
{
  "notifications": [
    {
      "id": 1,
      "user_id": 2,
      "task_id": "507f1f77bcf86cd799439011",
      "message": "You have been assigned to task 'Complete project documentation' by John Doe",
      "type": "task_assigned",
      "is_read": false,
      "created_at": "2024-01-15T10:30:00.000Z"
    },
    {
      "id": 2,
      "user_id": 2,
      "task_id": "507f1f77bcf86cd799439012",
      "message": "Task 'Review code changes' status has been updated to 'in_progress'",
      "type": "task_updated",
      "is_read": true,
      "created_at": "2024-01-15T09:15:00.000Z"
    }
  ],
  "total": 2
}
```

#### Error Responses

**400 Bad Request** - Invalid parameters:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Limit must be between 1 and 100"
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
curl -X GET "http://localhost:8003/api/v1/notifications?unread_only=true&limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Mark Notification as Read

Mark a specific notification as read.

**Endpoint**: `PUT /api/v1/notifications/{notification_id}/read`  
**Authentication**: JWT Bearer Token required

#### Path Parameters

| Parameter       | Type | Required | Description     |
| --------------- | ---- | -------- | --------------- |
| notification_id | int  | Yes      | Notification ID |

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (204 No Content)

No response body.

#### Error Responses

**403 Forbidden** - Access denied:

```json
{
  "error": {
    "code": "ACCESS_DENIED",
    "message": "Access denied to this notification"
  }
}
```

**404 Not Found** - Notification not found:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Notification not found"
  }
}
```

#### cURL Example

```bash
curl -X PUT http://localhost:8003/api/v1/notifications/1/read \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Mark All Notifications as Read

Mark all unread notifications for the authenticated user as read.

**Endpoint**: `PUT /api/v1/notifications/read-all`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (200 OK)

```json
{
  "marked_as_read": 5
}
```

#### Error Responses

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
curl -X PUT http://localhost:8003/api/v1/notifications/read-all \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Health Check Endpoints

### Comprehensive Health Check

**Endpoint**: `GET /health`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "notification-service",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 35.8
    },
    "disk": {
      "status": "healthy",
      "usage_percent": 67.8
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
  "service": "notification-service",
  "version": "1.0.0"
}
```

## Metrics Endpoint

**Endpoint**: `GET /metrics`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "notification-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "request_count": 850,
  "error_count": 12,
  "average_response_time_ms": 95.4,
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
| INTERNAL_ERROR       | 500         | Internal server error        |

## Rate Limiting

The Notification Service implements rate limiting:

- **Limit**: 150 requests per minute per IP
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

- **Swagger UI**: `http://localhost:8003/docs`
- **ReDoc**: `http://localhost:8003/redoc`
- **OpenAPI JSON**: `http://localhost:8003/openapi.json`

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require("axios");

class NotificationServiceClient {
  constructor(baseURL = "http://localhost:8003") {
    this.client = axios.create({ baseURL });
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  // Internal service method (no auth required)
  async createNotification(notificationData) {
    const response = await this.client.post(
      "/api/v1/notifications",
      notificationData
    );
    return response.data;
  }

  // Authenticated user methods
  async getNotifications(options = {}) {
    const { unread_only = false, limit = 50 } = options;
    const params = { unread_only, limit };

    const response = await this.client.get("/api/v1/notifications", {
      headers: { Authorization: `Bearer ${this.token}` },
      params,
    });
    return response.data;
  }

  async markNotificationAsRead(notificationId) {
    await this.client.put(
      `/api/v1/notifications/${notificationId}/read`,
      {},
      {
        headers: { Authorization: `Bearer ${this.token}` },
      }
    );
  }

  async markAllNotificationsAsRead() {
    const response = await this.client.put(
      "/api/v1/notifications/read-all",
      {},
      {
        headers: { Authorization: `Bearer ${this.token}` },
      }
    );
    return response.data;
  }

  // Health check methods
  async getHealth() {
    const response = await this.client.get("/health");
    return response.data;
  }

  async getSimpleHealth() {
    const response = await this.client.get("/health/simple");
    return response.data;
  }
}
```

### Python

```python
import requests
from typing import Optional, Dict, Any, List

class NotificationServiceClient:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def set_token(self, token: str):
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    # Internal service method (no auth required)
    def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/notifications",
            json=notification_data
        )
        response.raise_for_status()
        return response.json()

    # Authenticated user methods
    def get_notifications(
        self,
        unread_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        params = {"unread_only": unread_only, "limit": limit}

        response = requests.get(
            f"{self.base_url}/api/v1/notifications",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def mark_notification_as_read(self, notification_id: int) -> None:
        response = requests.put(
            f"{self.base_url}/api/v1/notifications/{notification_id}/read",
            headers=self._get_headers()
        )
        response.raise_for_status()

    def mark_all_notifications_as_read(self) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}/api/v1/notifications/read-all",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    # Health check methods
    def get_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_simple_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health/simple")
        response.raise_for_status()
        return response.json()
```

## Service Integration Examples

### Task Service Integration

Example of how the Task Service creates notifications:

```python
# In Task Service - when assigning a task
import aiohttp

async def notify_task_assignment(user_id: int, task_id: str, task_title: str, assigner_name: str):
    notification_data = {
        "user_id": user_id,
        "task_id": task_id,
        "message": f"You have been assigned to task '{task_title}' by {assigner_name}",
        "type": "task_assigned"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://notification-service:8003/api/v1/notifications",
            json=notification_data
        ) as response:
            if response.status == 201:
                return await response.json()
            else:
                # Handle error gracefully
                logger.error(f"Failed to create notification: {response.status}")
                return None
```

### Frontend Integration

Example of how the frontend polls for notifications:

```javascript
// In React frontend - notification polling
class NotificationManager {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.pollInterval = null;
  }

  startPolling(intervalMs = 30000) {
    this.pollInterval = setInterval(async () => {
      try {
        const result = await this.apiClient.getNotifications({
          unread_only: true,
        });
        // Update UI with new notifications
        this.updateNotificationUI(result.notifications);
      } catch (error) {
        console.error("Failed to fetch notifications:", error);
      }
    }, intervalMs);
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  async markAsRead(notificationId) {
    try {
      await this.apiClient.markNotificationAsRead(notificationId);
      // Update UI to reflect read status
      this.updateNotificationReadStatus(notificationId);
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  }
}
```
