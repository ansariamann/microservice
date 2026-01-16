"""
Shared logging configuration for all microservices
"""
import logging
import logging.config
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add service name if available
        service_name = os.getenv("SERVICE_NAME", "unknown")
        log_entry["service"] = service_name
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class HealthCheckFormatter(logging.Formatter):
    """Simple formatter for health check logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        return f"{datetime.utcnow().isoformat()}Z [{record.levelname}] {record.getMessage()}"


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    enable_json_logging: bool = True,
    log_file: str = None
) -> None:
    """
    Setup logging configuration for a microservice
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json_logging: Whether to use JSON formatting
        log_file: Optional log file path
    """
    # Set service name environment variable
    os.environ["SERVICE_NAME"] = service_name
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "simple": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "health": {
                "()": HealthCheckFormatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if enable_json_logging else "simple",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "health": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if enable_json_logging else "simple",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, user_id: int = None, request_id: str = None):
    """Log an incoming request"""
    extra = {}
    if user_id:
        extra["user_id"] = user_id
    if request_id:
        extra["request_id"] = request_id
    
    logger.info(f"Request: {method} {path}", extra=extra)


def log_response(logger: logging.Logger, method: str, path: str, status_code: int, duration: float, user_id: int = None, request_id: str = None):
    """Log a response"""
    extra = {
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2)
    }
    if user_id:
        extra["user_id"] = user_id
    if request_id:
        extra["request_id"] = request_id
    
    logger.info(f"Response: {method} {path} - {status_code} ({duration:.3f}s)", extra=extra)


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log an error with context"""
    extra = {"error_type": type(error).__name__}
    if context:
        extra.update(context)
    
    logger.error(f"Error: {str(error)}", extra=extra, exc_info=True)


def log_security_event(logger: logging.Logger, event_type: str, details: Dict[str, Any]):
    """Log a security-related event"""
    extra = {
        "security_event": event_type,
        **details
    }
    
    logger.warning(f"Security event: {event_type}", extra=extra)


def log_performance_metric(logger: logging.Logger, metric_name: str, value: float, unit: str = "ms", tags: Dict[str, str] = None):
    """Log a performance metric"""
    extra = {
        "metric_name": metric_name,
        "metric_value": value,
        "metric_unit": unit
    }
    if tags:
        extra["metric_tags"] = tags
    
    logger.info(f"Metric: {metric_name} = {value}{unit}", extra=extra)