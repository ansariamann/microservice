# User Service API Documentation

## Overview

The User Service provides authentication and user profile management functionality for the task management system. It handles user registration, login, and profile operations with JWT-based authentication.

**Base URL**: `http://localhost:8001`  
**API Version**: v1  
**Authentication**: JWT Bearer Token (except for registration and login)

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

## API Endpoints

### 1. User Registration

Register a new user account.

**Endpoint**: `POST /api/v1/register`  
**Authentication**: None required

#### Request Body

```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123",
  "name": "John Doe"
}
```

#### Request Schema

| Field    | Type   | Required | Validation                                 | Description          |
| -------- | ------ | -------- | ------------------------------------------ | -------------------- |
| email    | string | Yes      | Valid email format                         | User's email address |
| password | string | Yes      | Min 8 chars, must contain letter and digit | User's password      |
| name     | string | Yes      | 1-255 characters, non-empty                | User's full name     |

#### Response (201 Created)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "john.doe@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
}
```

#### Error Responses

**400 Bad Request** - Registration error:

```json
{
  "error": {
    "code": "REGISTRATION_ERROR",
    "message": "Email already exists"
  }
}
```

**400 Bad Request** - Validation error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password must contain at least one digit",
    "details": {
      "field": "password"
    }
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8001/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123",
    "name": "John Doe"
  }'
```

### 2. User Login

Authenticate a user and receive a JWT token.

**Endpoint**: `POST /api/v1/login`  
**Authentication**: None required

#### Request Body

```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123"
}
```

#### Request Schema

| Field    | Type   | Required | Description          |
| -------- | ------ | -------- | -------------------- |
| email    | string | Yes      | User's email address |
| password | string | Yes      | User's password      |

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "john.doe@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
}
```

#### Error Responses

**401 Unauthorized** - Invalid credentials:

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid email or password"
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8001/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123"
  }'
```

### 3. Get User Profile

Retrieve the current authenticated user's profile information.

**Endpoint**: `GET /api/v1/profile`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (200 OK)

```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "name": "John Doe",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T10:30:00.000Z"
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
curl -X GET http://localhost:8001/api/v1/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Update User Profile

Update the current authenticated user's profile information.

**Endpoint**: `PUT /api/v1/profile`  
**Authentication**: JWT Bearer Token required

#### Request Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

#### Request Body

```json
{
  "name": "John Smith",
  "email": "john.smith@example.com"
}
```

#### Request Schema

| Field | Type   | Required | Validation                     | Description          |
| ----- | ------ | -------- | ------------------------------ | -------------------- |
| name  | string | No       | 1-255 characters if provided   | User's full name     |
| email | string | No       | Valid email format if provided | User's email address |

#### Response (200 OK)

```json
{
  "id": 1,
  "email": "john.smith@example.com",
  "name": "John Smith",
  "created_at": "2024-01-15T10:30:00.000Z",
  "updated_at": "2024-01-15T14:45:00.000Z"
}
```

#### Error Responses

**400 Bad Request** - Update error:

```json
{
  "error": {
    "code": "PROFILE_UPDATE_ERROR",
    "message": "Email already exists"
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
curl -X PUT http://localhost:8001/api/v1/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john.smith@example.com"
  }'
```

## Health Check Endpoints

### Comprehensive Health Check

**Endpoint**: `GET /health`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "user-service",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 45.2
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
  "service": "user-service",
  "version": "1.0.0"
}
```

## Metrics Endpoint

**Endpoint**: `GET /metrics`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "user-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "request_count": 1250,
  "error_count": 23,
  "average_response_time_ms": 145.7,
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
| REGISTRATION_ERROR   | 400         | User registration failed     |
| AUTHENTICATION_ERROR | 401         | Invalid credentials or token |
| PROFILE_UPDATE_ERROR | 400         | Profile update failed        |
| VALIDATION_ERROR     | 400         | Request validation failed    |
| INTERNAL_ERROR       | 500         | Internal server error        |

## Rate Limiting

The User Service implements rate limiting:

- **Limit**: 100 requests per minute per IP
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

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- **OpenAPI JSON**: `http://localhost:8001/openapi.json`

## SDK Examples

### JavaScript/Node.js

```javascript
const axios = require("axios");

class UserServiceClient {
  constructor(baseURL = "http://localhost:8001") {
    this.client = axios.create({ baseURL });
    this.token = null;
  }

  async register(email, password, name) {
    const response = await this.client.post("/api/v1/register", {
      email,
      password,
      name,
    });
    this.token = response.data.access_token;
    return response.data;
  }

  async login(email, password) {
    const response = await this.client.post("/api/v1/login", {
      email,
      password,
    });
    this.token = response.data.access_token;
    return response.data;
  }

  async getProfile() {
    const response = await this.client.get("/api/v1/profile", {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return response.data;
  }

  async updateProfile(updates) {
    const response = await this.client.put("/api/v1/profile", updates, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return response.data;
  }
}
```

### Python

```python
import requests
from typing import Optional, Dict, Any

class UserServiceClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/register",
            json={"email": email, "password": password, "name": name}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def get_profile(self) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/profile",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()

    def update_profile(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}/api/v1/profile",
            json=updates,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()
```
