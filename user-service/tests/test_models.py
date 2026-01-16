"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models import User


class TestUserModel:
    """Test cases for User model"""

    def test_create_user(self, db_session):
        """Test creating a new user"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.name == "Test User"
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique_constraint(self, db_session):
        """Test that email must be unique"""
        user1 = User(
            email="test@example.com",
            password_hash="hashed_password1",
            name="Test User 1"
        )
        user2 = User(
            email="test@example.com",
            password_hash="hashed_password2",
            name="Test User 2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_required_fields(self, db_session):
        """Test that required fields cannot be null"""
        # Test missing email
        user = User(
            password_hash="hashed_password",
            name="Test User"
        )
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing password_hash
        user = User(
            email="test@example.com",
            name="Test User"
        )
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Test missing name
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        expected_repr = f"<User(id={user.id}, email='test@example.com', name='Test User')>"
        assert repr(user) == expected_repr

    def test_user_timestamps(self, db_session):
        """Test that timestamps are automatically set"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_update_timestamp(self, db_session):
        """Test that updated_at changes when user is modified"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Update user
        user.name = "Updated User"
        db_session.commit()
        db_session.refresh(user)
        
        assert user.updated_at > original_updated_at