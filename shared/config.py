"""
Shared configuration settings for all microservices
"""
import os
from typing import List


class BaseConfig:
    """Base configuration class with common settings"""
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Service Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:8080"
    ).split(",")
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        required_vars = ["JWT_SECRET"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var) or getattr(cls, var) == "your-secret-key-change-in-production":
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing or invalid required configuration: {', '.join(missing_vars)}")
        
        return True


class DatabaseConfig:
    """Database configuration utilities"""
    
    @staticmethod
    def get_postgres_url(
        host: str = None,
        port: str = None,
        database: str = None,
        username: str = None,
        password: str = None
    ) -> str:
        """Generate PostgreSQL connection URL"""
        host = host or os.getenv("DB_HOST", "localhost")
        port = port or os.getenv("DB_PORT", "5432")
        database = database or os.getenv("DB_NAME", "userdb")
        username = username or os.getenv("DB_USER", "user")
        password = password or os.getenv("DB_PASSWORD", "password")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def get_mongodb_url(
        host: str = None,
        port: str = None,
        database: str = None
    ) -> str:
        """Generate MongoDB connection URL"""
        host = host or os.getenv("MONGODB_HOST", "localhost")
        port = port or os.getenv("MONGODB_PORT", "27017")
        database = database or os.getenv("MONGODB_DATABASE", "taskdb")
        
        return f"mongodb://{host}:{port}/{database}"
    
    @staticmethod
    def get_sqlite_url(db_path: str = None) -> str:
        """Generate SQLite connection URL"""
        db_path = db_path or os.getenv("DB_PATH", "notifications.db")
        return f"sqlite:///{db_path}"


class ServiceConfig:
    """Service discovery and communication configuration"""
    
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
    TASK_SERVICE_URL: str = os.getenv("TASK_SERVICE_URL", "http://localhost:8002")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8003")
    
    # Service ports
    USER_SERVICE_PORT: int = int(os.getenv("USER_SERVICE_PORT", "8001"))
    TASK_SERVICE_PORT: int = int(os.getenv("TASK_SERVICE_PORT", "8002"))
    NOTIFICATION_SERVICE_PORT: int = int(os.getenv("NOTIFICATION_SERVICE_PORT", "8003"))
    
    # Request timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    RETRY_ATTEMPTS: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))