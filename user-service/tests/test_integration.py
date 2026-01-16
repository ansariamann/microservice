"""
Integration tests for User Service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base
from app.database import get_db


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


class TestUserRegistrationFlow:
    """Integration tests for user registration workflow"""

    def test_register_user_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
        assert "id" in user
        assert "created_at" in user
        assert "updated_at" in user

    def test_register_user_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        
        # Register first user
        response1 = client.post("/api/v1/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to register second user with same email
        user_data2 = {
            "email": "test@example.com",
            "password": "password456",
            "name": "Another User"
        }
        
        response2 = client.post("/api/v1/register", json=user_data2)
        assert response2.status_code == 400
        
        data = response2.json()
        assert "error" in data
        assert data["error"]["code"] == "REGISTRATION_ERROR"

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/register", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_register_user_short_password(self, client):
        """Test registration with short password"""
        user_data = {
            "email": "test@example.com",
            "password": "short",
            "name": "Test User"
        }
        
        response = client.post("/api/v1/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestUserAuthenticationFlow:
    """Integration tests for user authentication workflow"""

    def test_login_user_success(self, client):
        """Test successful user login"""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        client.post("/api/v1/register", json=user_data)
        
        # Login
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        user = data["user"]
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"

    def test_login_user_invalid_email(self, client):
        """Test login with invalid email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    def test_login_user_invalid_password(self, client):
        """Test login with invalid password"""
        # Register user first
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        client.post("/api/v1/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"


class TestUserProfileFlow:
    """Integration tests for user profile management workflow"""

    def test_get_profile_success(self, client):
        """Test successful profile retrieval"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        register_response = client.post("/api/v1/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_profile_no_token(self, client):
        """Test profile retrieval without token"""
        response = client.get("/api/v1/profile")
        
        assert response.status_code == 403  # No authorization header

    def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/profile", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_update_profile_success(self, client):
        """Test successful profile update"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        register_response = client.post("/api/v1/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Update profile
        update_data = {
            "name": "Updated User",
            "email": "updated@example.com"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/v1/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated User"
        assert data["email"] == "updated@example.com"

    def test_update_profile_partial(self, client):
        """Test partial profile update"""
        # Register user
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        register_response = client.post("/api/v1/register", json=user_data)
        token = register_response.json()["access_token"]
        
        # Update only name
        update_data = {"name": "Updated User"}
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/v1/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated User"
        assert data["email"] == "test@example.com"  # Should remain unchanged

    def test_update_profile_duplicate_email(self, client):
        """Test profile update with duplicate email"""
        # Register first user
        user_data1 = {
            "email": "user1@example.com",
            "password": "password123",
            "name": "User 1"
        }
        client.post("/api/v1/register", json=user_data1)
        
        # Register second user
        user_data2 = {
            "email": "user2@example.com",
            "password": "password123",
            "name": "User 2"
        }
        register_response2 = client.post("/api/v1/register", json=user_data2)
        token2 = register_response2.json()["access_token"]
        
        # Try to update second user's email to first user's email
        update_data = {"email": "user1@example.com"}
        headers = {"Authorization": f"Bearer {token2}"}
        response = client.put("/api/v1/profile", json=update_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "PROFILE_UPDATE_ERROR"


class TestCompleteUserWorkflow:
    """Integration tests for complete user workflows"""

    def test_complete_user_lifecycle(self, client):
        """Test complete user lifecycle: register -> login -> get profile -> update profile"""
        # 1. Register user
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        }
        register_response = client.post("/api/v1/register", json=user_data)
        assert register_response.status_code == 201
        
        register_token = register_response.json()["access_token"]
        user_id = register_response.json()["user"]["id"]
        
        # 2. Login user
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        login_response = client.post("/api/v1/login", json=login_data)
        assert login_response.status_code == 200
        
        login_token = login_response.json()["access_token"]
        assert login_response.json()["user"]["id"] == user_id
        
        # 3. Get profile with register token
        headers = {"Authorization": f"Bearer {register_token}"}
        profile_response = client.get("/api/v1/profile", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["id"] == user_id
        
        # 4. Get profile with login token
        headers = {"Authorization": f"Bearer {login_token}"}
        profile_response2 = client.get("/api/v1/profile", headers=headers)
        assert profile_response2.status_code == 200
        assert profile_response2.json()["id"] == user_id
        
        # 5. Update profile
        update_data = {
            "name": "Updated Test User",
            "email": "updated@example.com"
        }
        update_response = client.put("/api/v1/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_profile = update_response.json()
        assert updated_profile["name"] == "Updated Test User"
        assert updated_profile["email"] == "updated@example.com"
        assert updated_profile["id"] == user_id
        
        # 6. Verify profile was updated
        final_profile_response = client.get("/api/v1/profile", headers=headers)
        assert final_profile_response.status_code == 200
        
        final_profile = final_profile_response.json()
        assert final_profile["name"] == "Updated Test User"
        assert final_profile["email"] == "updated@example.com"


class TestHealthCheck:
    """Integration tests for health check endpoint"""

    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "user-service"
        assert data["version"] == "1.0.0"
        assert "database" in data


class TestAPIDocumentation:
    """Integration tests for API documentation"""

    def test_openapi_docs_available(self, client):
        """Test that OpenAPI documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs_available(self, client):
        """Test that ReDoc documentation is available"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        
        # Check that our endpoints are documented
        paths = data["paths"]
        assert "/api/v1/register" in paths
        assert "/api/v1/login" in paths
        assert "/api/v1/profile" in paths
        assert "/health" in paths