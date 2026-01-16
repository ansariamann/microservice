"""
Performance monitoring and metrics collection for microservices
"""
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = "count"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "tags": self.tags,
            "unit": self.unit
        }


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float
    unit: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
            # Also store as time series
            self.metrics[key].append(MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                unit="count"
            ))
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self.lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
            # Also store as time series
            self.metrics[key].append(MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                unit="gauge"
            ))
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = "ms"):
        """Record a histogram value (for timing, sizes, etc.)"""
        with self.lock:
            key = self._make_key(name, tags)
            self.histograms[key].append(value)
            
            # Keep only recent values to prevent memory growth
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            
            # Also store as time series
            self.metrics[key].append(MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags or {},
                unit=unit
            ))
    
    def record_timing(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timing metric"""
        self.record_histogram(name, duration_ms, tags, "ms")
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get current counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get current gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key, 0.0)
    
    def get_histogram_summary(self, name: str, tags: Dict[str, str] = None) -> Optional[MetricSummary]:
        """Get histogram summary statistics"""
        key = self._make_key(name, tags)
        values = self.histograms.get(key, [])
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return MetricSummary(
            name=name,
            count=count,
            sum=sum(sorted_values),
            min=min(sorted_values),
            max=max(sorted_values),
            avg=sum(sorted_values) / count,
            p50=self._percentile(sorted_values, 50),
            p95=self._percentile(sorted_values, 95),
            p99=self._percentile(sorted_values, 99),
            unit="ms"
        )
    
    def get_recent_metrics(self, name: str = None, since: datetime = None, limit: int = 100) -> List[MetricPoint]:
        """Get recent metric points"""
        if since is None:
            since = datetime.utcnow() - timedelta(hours=1)
        
        results = []
        
        for key, points in self.metrics.items():
            if name and not key.startswith(name):
                continue
            
            for point in points:
                if point.timestamp >= since:
                    results.append(point)
        
        # Sort by timestamp and limit
        results.sort(key=lambda p: p.timestamp, reverse=True)
        return results[:limit]
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }
        
        for key, values in self.histograms.items():
            if values:
                sorted_values = sorted(values)
                count = len(sorted_values)
                summary["histograms"][key] = {
                    "count": count,
                    "min": min(sorted_values),
                    "max": max(sorted_values),
                    "avg": sum(sorted_values) / count,
                    "p95": self._percentile(sorted_values, 95),
                    "p99": self._percentile(sorted_values, 99)
                }
        
        return summary
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.metrics.clear()
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for metric with tags"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        
        if lower == upper:
            return sorted_values[lower]
        
        # Linear interpolation
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_timing(self.metric_name, duration_ms, self.tags)
            
            # Add error tag if exception occurred
            if exc_type:
                error_tags = {**self.tags, "error": "true", "error_type": exc_type.__name__}
                self.collector.increment_counter(f"{self.metric_name}.errors", 1.0, error_tags)


@asynccontextmanager
async def async_timing_context(collector: MetricsCollector, metric_name: str, tags: Dict[str, str] = None):
    """Async context manager for timing operations"""
    start_time = time.time()
    tags = tags or {}
    
    try:
        yield
    except Exception as e:
        # Add error tag if exception occurred
        error_tags = {**tags, "error": "true", "error_type": type(e).__name__}
        collector.increment_counter(f"{metric_name}.errors", 1.0, error_tags)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        collector.record_timing(metric_name, duration_ms, tags)


def timing_decorator(collector: MetricsCollector, metric_name: str = None, tags: Dict[str, str] = None):
    """Decorator for timing function calls"""
    def decorator(func: Callable):
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                async with async_timing_context(collector, name, tags):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with TimingContext(collector, name, tags):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions using global collector
def increment_counter(name: str, value: float = 1.0, tags: Dict[str, str] = None):
    """Increment a counter metric"""
    metrics_collector.increment_counter(name, value, tags)


def set_gauge(name: str, value: float, tags: Dict[str, str] = None):
    """Set a gauge metric value"""
    metrics_collector.set_gauge(name, value, tags)


def record_timing(name: str, duration_ms: float, tags: Dict[str, str] = None):
    """Record a timing metric"""
    metrics_collector.record_timing(name, duration_ms, tags)


def record_histogram(name: str, value: float, tags: Dict[str, str] = None, unit: str = "ms"):
    """Record a histogram value"""
    metrics_collector.record_histogram(name, value, tags, unit)


def time_operation(name: str, tags: Dict[str, str] = None):
    """Context manager for timing operations"""
    return TimingContext(metrics_collector, name, tags)


def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of all metrics"""
    return metrics_collector.get_all_metrics_summary()


def get_recent_metrics(name: str = None, since: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent metric points"""
    points = metrics_collector.get_recent_metrics(name, since, limit)
    return [point.to_dict() for point in points]