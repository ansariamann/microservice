"""
Database connection and configuration for Task Service.
Uses Motor (async MongoDB driver) for database operations.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    mongodb_url: str = "mongodb://localhost:27017/taskdb"
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "taskdb"
    
    class Config:
        env_file = ".env"


class DatabaseManager:
    """Manages MongoDB connection and database operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.settings = DatabaseSettings()
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.settings.mongodb_url)
            self.database = self.client[self.settings.mongodb_database]
            
            # Test the connection
            await self.client.admin.command('ping')
            self.logger.info(f"Connected to MongoDB at {self.settings.mongodb_url}")
            
            # Create indexes
            await self._create_indexes()
            
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimal query performance."""
        if self.database is None:
            return
        
        tasks_collection = self.database.tasks
        
        # Create indexes for common query patterns
        await tasks_collection.create_index("creator_id")
        await tasks_collection.create_index("assignee_id")
        await tasks_collection.create_index("status")
        await tasks_collection.create_index("due_date")
        await tasks_collection.create_index([("creator_id", 1), ("status", 1)])
        await tasks_collection.create_index([("assignee_id", 1), ("status", 1)])
        
        self.logger.info("Database indexes created successfully")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if self.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.client is not None and self.database is not None


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency function to get database instance."""
    return db_manager.get_database()