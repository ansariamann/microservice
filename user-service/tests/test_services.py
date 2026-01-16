"""
Unit tests for user services
"""
import pytest
from unittest.mock import patch

from app.models import User
from app.schemas import UserRegistration, UserLogin, UserProfileUpdate
from app.services import UserService


class TestUserService:
    """Test cases for UserService class"""

    def test_register_user_success(self, db_session):
        """Test successful user registration"""
        user_service = UserService(db_session)
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        token_response = user_service.register_user(user_data)
        
        # Check token response
        assert token_response.access_token is not None
        assert token_response.token_type == "bearer"
        assert token_response.user.email == "test@example.com"
        assert token_response.user.name == "Test User"
        
        # Check user was created in database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.password_hash != "password123"  # Should be hashed

    def test_register_user_duplicate_email(self, db_session):
        """Test user registration with duplicate email"""
        user_service = UserService(db_session)
        
        # Create first user
        user_data1 = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User 1"
        )
        user_service.register_user(user_data1)
        
        # Try to create second user with same email
        user_data2 = UserRegistration(
            email="test@example.com",
            password="password456",
            name="Test User 2"
        )
        
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.register_user(user_data2)

    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        user_service.register_user(user_data)
        
        # Authenticate user
        login_data = UserLogin(
            email="test@example.com",
            password="password123"
        )
        
        token_response = user_service.authenticate_user(login_data)
        
        # Check token response
        assert token_response.access_token is not None
        assert token_response.token_type == "bearer"
        assert token_response.user.email == "test@example.com"
        assert token_response.user.name == "Test User"

    def test_authenticate_user_invalid_email(self, db_session):
        """Test authentication with invalid email"""
        user_service = UserService(db_session)
        
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="password123"
        )
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_service.authenticate_user(login_data)

    def test_authenticate_user_invalid_password(self, db_session):
        """Test authentication with invalid password"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        user_service.register_user(user_data)
        
        # Try to authenticate with wrong password
        login_data = UserLogin(
            email="test@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            user_service.authenticate_user(login_data)

    def test_get_user_by_id(self, db_session):
        """Test getting user by ID"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        user_id = token_response.user.id
        
        # Get user by ID
        user = user_service.get_user_by_id(user_id)
        
        assert user is not None
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_get_user_by_id_not_found(self, db_session):
        """Test getting user by non-existent ID"""
        user_service = UserService(db_session)
        
        user = user_service.get_user_by_id(999)
        
        assert user is None

    def test_get_user_by_email(self, db_session):
        """Test getting user by email"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        user_service.register_user(user_data)
        
        # Get user by email
        user = user_service.get_user_by_email("test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_get_user_by_email_not_found(self, db_session):
        """Test getting user by non-existent email"""
        user_service = UserService(db_session)
        
        user = user_service.get_user_by_email("nonexistent@example.com")
        
        assert user is None

    def test_password_is_hashed(self, db_session):
        """Test that password is properly hashed during registration"""
        user_service = UserService(db_session)
        password = "password123"
        
        user_data = UserRegistration(
            email="test@example.com",
            password=password,
            name="Test User"
        )
        
        user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        
        # Password should be hashed, not stored in plain text
        assert user.password_hash != password
        assert len(user.password_hash) >= 50  # bcrypt hashes are typically 60 chars

    def test_jwt_token_contains_user_info(self, db_session):
        """Test that JWT token contains correct user information"""
        user_service = UserService(db_session)
        
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        token_response = user_service.register_user(user_data)
        
        # Decode token to verify contents
        from app.auth import jwt_manager
        payload = jwt_manager.decode_token(token_response.access_token)
        
        assert payload is not None
        assert payload["user_id"] == token_response.user.id
        assert payload["email"] == "test@example.com"

    def test_get_user_profile(self, db_session):
        """Test getting user profile"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Get profile
        profile = user_service.get_user_profile(user)
        
        assert profile.id == user.id
        assert profile.email == "test@example.com"
        assert profile.name == "Test User"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_update_user_profile_name_only(self, db_session):
        """Test updating user profile name only"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Update profile
        update_data = UserProfileUpdate(name="Updated User")
        updated_profile = user_service.update_user_profile(user, update_data)
        
        assert updated_profile.name == "Updated User"
        assert updated_profile.email == "test@example.com"  # Should remain unchanged
        
        # Verify in database
        db_session.refresh(user)
        assert user.name == "Updated User"
        assert user.email == "test@example.com"

    def test_update_user_profile_email_only(self, db_session):
        """Test updating user profile email only"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Update profile
        update_data = UserProfileUpdate(email="updated@example.com")
        updated_profile = user_service.update_user_profile(user, update_data)
        
        assert updated_profile.email == "updated@example.com"
        assert updated_profile.name == "Test User"  # Should remain unchanged
        
        # Verify in database
        db_session.refresh(user)
        assert user.email == "updated@example.com"
        assert user.name == "Test User"

    def test_update_user_profile_both_fields(self, db_session):
        """Test updating both name and email"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Update profile
        update_data = UserProfileUpdate(
            name="Updated User",
            email="updated@example.com"
        )
        updated_profile = user_service.update_user_profile(user, update_data)
        
        assert updated_profile.name == "Updated User"
        assert updated_profile.email == "updated@example.com"
        
        # Verify in database
        db_session.refresh(user)
        assert user.name == "Updated User"
        assert user.email == "updated@example.com"

    def test_update_user_profile_duplicate_email(self, db_session):
        """Test updating user profile with duplicate email"""
        user_service = UserService(db_session)
        
        # Register first user
        user_data1 = UserRegistration(
            email="user1@example.com",
            password="password123",
            name="User 1"
        )
        user_service.register_user(user_data1)
        
        # Register second user
        user_data2 = UserRegistration(
            email="user2@example.com",
            password="password123",
            name="User 2"
        )
        token_response2 = user_service.register_user(user_data2)
        
        # Get second user from database
        user2 = db_session.query(User).filter(User.id == token_response2.user.id).first()
        
        # Try to update second user's email to first user's email
        update_data = UserProfileUpdate(email="user1@example.com")
        
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.update_user_profile(user2, update_data)

    def test_update_user_profile_same_email(self, db_session):
        """Test updating user profile with same email (should be allowed)"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Update profile with same email (should be allowed)
        update_data = UserProfileUpdate(
            name="Updated User",
            email="test@example.com"  # Same email
        )
        updated_profile = user_service.update_user_profile(user, update_data)
        
        assert updated_profile.name == "Updated User"
        assert updated_profile.email == "test@example.com"

    def test_update_user_profile_empty_update(self, db_session):
        """Test updating user profile with no changes"""
        user_service = UserService(db_session)
        
        # Register user first
        user_data = UserRegistration(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        token_response = user_service.register_user(user_data)
        
        # Get user from database
        user = db_session.query(User).filter(User.id == token_response.user.id).first()
        
        # Update profile with no changes
        update_data = UserProfileUpdate()
        updated_profile = user_service.update_user_profile(user, update_data)
        
        # Should return current profile unchanged
        assert updated_profile.name == "Test User"
        assert updated_profile.email == "test@example.com"