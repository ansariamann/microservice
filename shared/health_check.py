"""
Comprehensive health check system for microservices
"""
import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class HealthChecker:
    """Health check manager for microservices"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, Callable] = {}
        self.start_time = time.time()
        self.last_check_time: Optional[datetime] = None
        self.check_history: List[Dict[str, Any]] = []
        self.max_history = 100
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function"""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_check(self, name: str, check_func: Callable) -> HealthCheckResult:
        """Run a single health check"""
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, dict):
                status = HealthStatus(result.get("status", HealthStatus.HEALTHY))
                message = result.get("message", "OK")
                details = result.get("details")
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
                details = None
            else:
                status = HealthStatus.HEALTHY
                message = str(result) if result else "OK"
                details = None
            
            return HealthCheckResult(
                name=name,
                status=status,
                message=message,
                duration_ms=round(duration_ms, 2),
                timestamp=timestamp,
                details=details
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {str(e)}")
            
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=round(duration_ms, 2),
                timestamp=timestamp,
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        self.last_check_time = datetime.utcnow()
        
        # Run all checks concurrently
        check_tasks = [
            self.run_check(name, check_func)
            for name, check_func in self.checks.items()
        ]
        
        results = await asyncio.gather(*check_tasks)
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        unhealthy_count = 0
        degraded_count = 0
        
        for result in results:
            if result.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
            elif result.status == HealthStatus.DEGRADED:
                degraded_count += 1
        
        # Determine overall status based on individual check results
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        # Create response
        health_response = {
            "service": self.service_name,
            "status": overall_status.value,
            "timestamp": self.last_check_time.isoformat() + "Z",
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "checks": {result.name: result.to_dict() for result in results},
            "system_metrics": system_metrics.to_dict(),
            "summary": {
                "total_checks": len(results),
                "healthy_checks": len([r for r in results if r.status == HealthStatus.HEALTHY]),
                "degraded_checks": degraded_count,
                "unhealthy_checks": unhealthy_count
            }
        }
        
        # Store in history
        self.check_history.append({
            "timestamp": self.last_check_time.isoformat() + "Z",
            "status": overall_status.value,
            "check_count": len(results),
            "unhealthy_count": unhealthy_count,
            "degraded_count": degraded_count
        })
        
        # Limit history size
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
        
        return health_response
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            
            return SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_percent, 2),
                memory_available_mb=round(memory_available_mb, 2),
                disk_usage_percent=round(disk_usage_percent, 2),
                uptime_seconds=round(uptime_seconds, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                uptime_seconds=round(time.time() - self.start_time, 2)
            )
    
    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health check history"""
        return self.check_history[-limit:]
    
    def is_healthy(self) -> bool:
        """Check if service is currently healthy"""
        if not self.last_check_time:
            return False
        
        # Consider service unhealthy if last check was more than 5 minutes ago
        if datetime.utcnow() - self.last_check_time > timedelta(minutes=5):
            return False
        
        # Check recent history
        if self.check_history:
            recent_status = self.check_history[-1]["status"]
            return recent_status == HealthStatus.HEALTHY.value
        
        return False


# Common health check functions
def database_health_check(db_connection_func: Callable) -> Callable:
    """Create a database health check function"""
    async def check():
        try:
            if asyncio.iscoroutinefunction(db_connection_func):
                result = await db_connection_func()
            else:
                result = db_connection_func()
            
            return {
                "status": HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                "message": "Database connection successful" if result else "Database connection failed"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database check failed: {str(e)}"
            }
    
    return check


def external_service_health_check(service_name: str, check_func: Callable) -> Callable:
    """Create an external service health check function"""
    async def check():
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            return {
                "status": HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                "message": f"{service_name} is {'available' if result else 'unavailable'}",
                "details": {"service": service_name}
            }
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"{service_name} check failed: {str(e)}",
                "details": {"service": service_name, "error": str(e)}
            }
    
    return check


def memory_usage_check(threshold_percent: float = 90.0) -> Callable:
    """Create a memory usage health check"""
    def check():
        try:
            memory = psutil.virtual_memory()
            if memory.percent > threshold_percent:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"High memory usage: {memory.percent:.1f}%",
                    "details": {"memory_percent": memory.percent, "threshold": threshold_percent}
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": f"Memory usage normal: {memory.percent:.1f}%",
                    "details": {"memory_percent": memory.percent}
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Memory check failed: {str(e)}"
            }
    
    return check


def disk_usage_check(threshold_percent: float = 90.0) -> Callable:
    """Create a disk usage health check"""
    def check():
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > threshold_percent:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"High disk usage: {disk.percent:.1f}%",
                    "details": {"disk_percent": disk.percent, "threshold": threshold_percent}
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": f"Disk usage normal: {disk.percent:.1f}%",
                    "details": {"disk_percent": disk.percent}
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Disk check failed: {str(e)}"
            }
    
    return check