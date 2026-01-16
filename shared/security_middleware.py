"""
Shared security middleware and utilities for all microservices
"""
import re
import time
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import html


logger = logging.getLogger(__name__)


class SecurityHeaders:
    """Security headers configuration"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


class InputSanitizer:
    """Input validation and sanitization utilities"""
    
    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bOR\s+\d+\s*=\s*\d+)",
        r"(\'\s*(OR|AND)\s*\'\w*\'\s*=\s*\'\w*\')",
    ]
    
    NOSQL_INJECTION_PATTERNS = [
        r"(\$where|\$ne|\$gt|\$lt|\$gte|\$lte|\$in|\$nin|\$regex)",
        r"(javascript:|eval\(|setTimeout\(|setInterval\()",
    ]
    
    XSS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:|vbscript:|onload=|onerror=|onclick=)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(<object[^>]*>.*?</object>)",
        r"(<embed[^>]*>.*?</embed>)",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value.strip()
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection attempts"""
        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_nosql_injection(cls, value: str) -> bool:
        """Detect potential NoSQL injection attempts"""
        for pattern in cls.NOSQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """Detect potential XSS attempts"""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_input(cls, value: Any, field_name: str = "input") -> Any:
        """Comprehensive input validation"""
        if isinstance(value, str):
            # Check for injection attempts
            if cls.detect_sql_injection(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name}: potential SQL injection detected"
                )
            
            if cls.detect_nosql_injection(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name}: potential NoSQL injection detected"
                )
            
            if cls.detect_xss(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid {field_name}: potential XSS detected"
                )
            
            return cls.sanitize_string(value)
        
        elif isinstance(value, dict):
            return {k: cls.validate_input(v, f"{field_name}.{k}") for k, v in value.items()}
        
        elif isinstance(value, list):
            return [cls.validate_input(item, f"{field_name}[{i}]") for i, item in enumerate(value)]
        
        return value


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True
    
    def get_reset_time(self, client_id: str) -> int:
        """Get time until rate limit resets"""
        client_requests = self.requests[client_id]
        if not client_requests:
            return 0
        
        oldest_request = client_requests[0]
        return int(oldest_request + self.window_seconds - time.time())


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI applications"""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.security_headers = SecurityHeaders.get_security_headers()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with security checks"""
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Rate limiting check
        if not self.rate_limiter.is_allowed(client_ip):
            reset_time = self.rate_limiter.get_reset_time(client_ip)
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            return Response(
                content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(reset_time),
                    **self.security_headers
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware for audit trails"""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response details"""
        start_time = time.time()
        
        # Log request
        client_ip = self._get_client_ip(request)
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"for {request.method} {request.url.path} "
            f"in {process_time:.3f}s"
        )
        
        # Log errors
        if response.status_code >= 400:
            logger.warning(
                f"Error response: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"from {client_ip}"
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize request data"""
    return InputSanitizer.validate_input(data, "request_data")


def create_security_middleware(
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    enable_request_logging: bool = True
) -> List[Any]:
    """Create security middleware stack"""
    middlewares = []
    
    # Rate limiting and security headers
    rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
    middlewares.append((SecurityMiddleware, {"rate_limiter": rate_limiter}))
    
    # Request logging
    if enable_request_logging:
        middlewares.append((RequestLoggingMiddleware, {}))
    
    return middlewares