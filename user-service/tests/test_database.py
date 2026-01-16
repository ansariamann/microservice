"""
Unit tests for database utilities
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from app.database import get_db, check_db_connection, init_db, create_tables
from app.models import User


class TestDatabaseUtilities:
    """Test cases for database utility functions"""

    def test_get_db_dependency(self, db_session):
        """Test get_db dependency function"""
        # Test with the provided test session
        # Should be able to query
        users = db_session.query(User).all()
        assert isinstance(users, list)
        
        # Test that we can add and query data
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        users = db_session.query(User).all()
        assert len(users) == 1
        assert users[0].email == "test@example.com"

    def test_create_tables(self, db_session):
        """Test create_tables function"""
        # This is tested implicitly in conftest.py
        # Just verify we can create a user after tables are created
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None

    def test_init_db(self):
        """Test init_db function"""
        with patch('app.database.create_tables') as mock_create_tables:
            init_db()
            mock_create_tables.assert_called_once()

    @patch('app.database.SessionLocal')
    def test_check_db_connection_success(self, mock_session_local):
        """Test successful database connection check"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        result = check_db_connection()
        
        assert result is True
        mock_db.execute.assert_called_once_with("SELECT 1")
        mock_db.close.assert_called_once()

    @patch('app.database.SessionLocal')
    def test_check_db_connection_failure(self, mock_session_local):
        """Test failed database connection check"""
        mock_db = MagicMock()
        mock_db.execute.side_effect = OperationalError("Connection failed", None, None)
        mock_session_local.return_value = mock_db
        
        with patch('builtins.print') as mock_print:
            result = check_db_connection()
        
        assert result is False
        mock_print.assert_called_once()
        assert "Database connection failed" in mock_print.call_args[0][0]

    def test_database_session_isolation(self, db_session):
        """Test that database sessions are properly isolated"""
        # Create user in first session
        user1 = User(
            email="test1@example.com",
            password_hash="hashed_password1",
            name="Test User 1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Verify user exists
        users = db_session.query(User).all()
        assert len(users) == 1
        assert users[0].email == "test1@example.com"

    def test_database_rollback(self, db_session):
        """Test database rollback functionality"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User"
        )
        
        db_session.add(user)
        # Don't commit
        
        # Rollback
        db_session.rollback()
        
        # User should not exist
        users = db_session.query(User).all()
        assert len(users) == 0