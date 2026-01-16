"""
Test cleanup utilities for managing test data and environments.

This module provides utilities for cleaning up test data, managing test
databases, and ensuring clean test environments across all services.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import httpx
import psycopg2
from pymongo import MongoClient
import sqlite3
import os
import tempfile
import shutil

logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """Base class for database cleanup operations."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def cleanup(self):
        """Clean up all test data."""
        raise NotImplementedError
    
    async def reset(self):
        """Reset database to initial state."""
        raise NotImplementedError


class PostgreSQLCleaner(DatabaseCleaner):
    """PostgreSQL database cleaner for User Service tests."""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.tables = ['users']  # Add more tables as needed
    
    async def cleanup(self):
        """Clean up all test data from PostgreSQL."""
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Disable foreign key checks temporarily
            cursor.execute("SET session_replication_role = replica;")
            
            # Clean up tables in reverse order to handle foreign keys
            for table in reversed(self.tables):
                cursor.execute(f"DELETE FROM {table};")
                cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")
            
            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("PostgreSQL test data cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to clean up PostgreSQL test data: {e}")
            raise
    
    async def reset(self):
        """Reset PostgreSQL database to initial state."""
        await self.cleanup()
    
    def create_test_database(self, db_name: str = "test_userdb"):
        """Create a test database."""
        try:
            # Connect to default database to create test database
            base_conn_string = self.connection_string.rsplit('/', 1)[0] + '/postgres'
            conn = psycopg2.connect(base_conn_string)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Drop test database if exists
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
            
            # Create test database
            cursor.execute(f"CREATE DATABASE {db_name};")
            
            cursor.close()
            conn.close()
            
            logger.info(f"Test database '{db_name}' created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test database: {e}")
            raise


class MongoDBCleaner(DatabaseCleaner):
    """MongoDB database cleaner for Task Service tests."""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.collections = ['tasks']  # Add more collections as needed
    
    async def cleanup(self):
        """Clean up all test data from MongoDB."""
        try:
            client = MongoClient(self.connection_string)
            db = client.get_default_database()
            
            # Clean up collections
            for collection_name in self.collections:
                collection = db[collection_name]
                result = collection.delete_many({})
                logger.info(f"Deleted {result.deleted_count} documents from {collection_name}")
            
            client.close()
            logger.info("MongoDB test data cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to clean up MongoDB test data: {e}")
            raise
    
    async def reset(self):
        """Reset MongoDB database to initial state."""
        await self.cleanup()
    
    def create_test_database(self, db_name: str = "test_taskdb"):
        """Create a test database (MongoDB creates databases automatically)."""
        try:
            client = MongoClient(self.connection_string)
            db = client[db_name]
            
            # Create a dummy document to ensure database creation
            db.test_collection.insert_one({"test": "data"})
            db.test_collection.delete_one({"test": "data"})
            
            client.close()
            logger.info(f"Test database '{db_name}' initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize test database: {e}")
            raise


class SQLiteCleaner(DatabaseCleaner):
    """SQLite database cleaner for Notification Service tests."""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.tables = ['notifications']  # Add more tables as needed
        # Extract file path from connection string
        self.db_path = connection_string.replace('sqlite:///', '')
    
    async def cleanup(self):
        """Clean up all test data from SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up tables
            for table in self.tables:
                cursor.execute(f"DELETE FROM {table};")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("SQLite test data cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Failed to clean up SQLite test data: {e}")
            raise
    
    async def reset(self):
        """Reset SQLite database to initial state."""
        await self.cleanup()
    
    def create_test_database(self, db_path: Optional[str] = None):
        """Create a test database file."""
        try:
            if db_path:
                self.db_path = db_path
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Create empty database file
            conn = sqlite3.connect(self.db_path)
            conn.close()
            
            logger.info(f"Test database '{self.db_path}' created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test database: {e}")
            raise


class ServiceCleaner:
    """Service-level cleaner for API-based cleanup."""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def cleanup_user_data(self, user_ids: List[int]):
        """Clean up user-related data via API."""
        async with httpx.AsyncClient() as client:
            for user_id in user_ids:
                try:
                    response = await client.delete(
                        f"{self.base_url}/api/v1/users/{user_id}",
                        headers=self.headers
                    )
                    if response.status_code in [200, 204, 404]:
                        logger.info(f"Cleaned up user {user_id}")
                    else:
                        logger.warning(f"Failed to clean up user {user_id}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error cleaning up user {user_id}: {e}")
    
    async def cleanup_task_data(self, task_ids: List[str]):
        """Clean up task-related data via API."""
        async with httpx.AsyncClient() as client:
            for task_id in task_ids:
                try:
                    response = await client.delete(
                        f"{self.base_url}/api/v1/tasks/{task_id}",
                        headers=self.headers
                    )
                    if response.status_code in [200, 204, 404]:
                        logger.info(f"Cleaned up task {task_id}")
                    else:
                        logger.warning(f"Failed to clean up task {task_id}: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error cleaning up task {task_id}: {e}")


class TestEnvironmentManager:
    """Manages complete test environment setup and cleanup."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cleaners = []
        self._setup_cleaners()
    
    def _setup_cleaners(self):
        """Set up database cleaners based on configuration."""
        if 'postgresql' in self.config:
            self.cleaners.append(
                PostgreSQLCleaner(self.config['postgresql']['connection_string'])
            )
        
        if 'mongodb' in self.config:
            self.cleaners.append(
                MongoDBCleaner(self.config['mongodb']['connection_string'])
            )
        
        if 'sqlite' in self.config:
            self.cleaners.append(
                SQLiteCleaner(self.config['sqlite']['connection_string'])
            )
    
    async def setup(self):
        """Set up test environment."""
        logger.info("Setting up test environment...")
        
        # Create test databases
        for cleaner in self.cleaners:
            if hasattr(cleaner, 'create_test_database'):
                cleaner.create_test_database()
        
        logger.info("Test environment setup completed")
    
    async def cleanup(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        
        # Clean up all databases
        cleanup_tasks = [cleaner.cleanup() for cleaner in self.cleaners]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info("Test environment cleanup completed")
    
    async def reset(self):
        """Reset test environment to initial state."""
        logger.info("Resetting test environment...")
        
        # Reset all databases
        reset_tasks = [cleaner.reset() for cleaner in self.cleaners]
        await asyncio.gather(*reset_tasks, return_exceptions=True)
        
        logger.info("Test environment reset completed")


class TempDirectoryManager:
    """Manages temporary directories for test files."""
    
    def __init__(self):
        self.temp_dirs = []
    
    def create_temp_dir(self, prefix: str = "test_") -> str:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()


@asynccontextmanager
async def test_environment(config: Dict[str, Any]):
    """Context manager for test environment setup and cleanup."""
    manager = TestEnvironmentManager(config)
    temp_manager = TempDirectoryManager()
    
    try:
        await manager.setup()
        yield manager, temp_manager
    finally:
        await manager.cleanup()
        temp_manager.cleanup()


# Convenience functions
async def cleanup_all_test_data(config: Dict[str, Any]):
    """Clean up all test data across all services."""
    async with test_environment(config) as (manager, _):
        await manager.cleanup()


def get_test_config() -> Dict[str, Any]:
    """Get test configuration from environment variables."""
    return {
        'postgresql': {
            'connection_string': os.getenv(
                'TEST_DATABASE_URL', 
                'postgresql://testuser:testpass@localhost:5433/test_userdb'
            )
        },
        'mongodb': {
            'connection_string': os.getenv(
                'TEST_MONGODB_URL', 
                'mongodb://localhost:27018/test_taskdb'
            )
        },
        'sqlite': {
            'connection_string': os.getenv(
                'TEST_SQLITE_URL', 
                'sqlite:///test_notifications.db'
            )
        }
    }


# Export commonly used classes and functions
__all__ = [
    'DatabaseCleaner', 'PostgreSQLCleaner', 'MongoDBCleaner', 'SQLiteCleaner',
    'ServiceCleaner', 'TestEnvironmentManager', 'TempDirectoryManager',
    'test_environment', 'cleanup_all_test_data', 'get_test_config'
]