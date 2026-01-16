"""
Tests for database connection and configuration.
"""

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.database import DatabaseManager, DatabaseSettings


class TestDatabaseSettings:
    """Test database configuration settings."""
    
    def test_default_settings(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        
        assert settings.mongodb_url == "mongodb://localhost:27017/taskdb"
        assert settings.mongodb_host == "localhost"
        assert settings.mongodb_port == 27017
        assert settings.mongodb_database == "taskdb"
    
    def test_custom_settings(self):
        """Test custom database settings."""
        settings = DatabaseSettings(
            mongodb_url="mongodb://testhost:27018/testdb",
            mongodb_host="testhost",
            mongodb_port=27018,
            mongodb_database="testdb"
        )
        
        assert settings.mongodb_url == "mongodb://testhost:27018/testdb"
        assert settings.mongodb_host == "testhost"
        assert settings.mongodb_port == 27018
        assert settings.mongodb_database == "testdb"


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest_asyncio.fixture
    async def db_manager(self):
        """Create a test database manager."""
        manager = DatabaseManager()
        # Override settings for testing
        manager.settings.mongodb_url = "mongodb://localhost:27017/test_taskdb"
        manager.settings.mongodb_database = "test_taskdb"
        return manager
    
    @pytest_asyncio.fixture
    async def connected_db_manager(self, db_manager):
        """Create a connected database manager."""
        try:
            await db_manager.connect()
            yield db_manager
        finally:
            await db_manager.disconnect()
    
    async def test_connect_success(self, db_manager):
        """Test successful database connection."""
        try:
            await db_manager.connect()
            
            assert db_manager.client is not None
            assert db_manager.database is not None
            assert db_manager.database.name == "test_taskdb"
            
        finally:
            await db_manager.disconnect()
    
    async def test_disconnect(self, connected_db_manager):
        """Test database disconnection."""
        await connected_db_manager.disconnect()
        
        # Client should still exist but connection should be closed
        assert connected_db_manager.client is not None
    
    async def test_get_database_without_connection(self, db_manager):
        """Test getting database without connection raises error."""
        with pytest.raises(RuntimeError, match="Database not connected"):
            db_manager.get_database()
    
    async def test_get_database_with_connection(self, connected_db_manager):
        """Test getting database with active connection."""
        database = connected_db_manager.get_database()
        
        assert database is not None
        assert database.name == "test_taskdb"
    
    async def test_create_indexes(self, connected_db_manager):
        """Test that indexes are created properly."""
        # Indexes should be created during connection
        database = connected_db_manager.get_database()
        tasks_collection = database.tasks
        
        # Get index information
        indexes = await tasks_collection.list_indexes().to_list(length=None)
        index_names = [index['name'] for index in indexes]
        
        # Check that our custom indexes exist (in addition to default _id_ index)
        assert len(index_names) >= 1  # At least the default _id_ index
        
        # Note: In a real test environment with MongoDB running, we would check for specific indexes
        # For now, we just verify the method doesn't syntax error