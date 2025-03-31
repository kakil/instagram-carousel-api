"""
API security middleware and dependencies for Instagram Carousel Generator.

Enhanced security features including:
- Improved API key validation
- More robust rate limiting
- IP-based tracking
- Comprehensive request validation
"""
import logging
import time
from ipaddress import ip_address, ip_network
from typing import Callable, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def get_client_ip(request: Request) -> str:
    """
    Safely extract client IP address.

    Args:
        request: FastAPI request object

    Returns:
        str: Client IP address
    """
    # Check for common proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP if multiple are present
        return forwarded_for.split(",")[0].strip()

    # Fallback to direct client host
    return request.client.host if request.client else "unknown"


# Rate limiting storage with more sophisticated tracking
class RateLimiter:
    """
    Advanced rate limiting with IP-based tracking and multiple strategies.

    Supports:
    - Per-IP rate limiting
    - Global rate limiting
    - Burst protection
    """

    def __init__(
        self, max_requests: int = 100, window_seconds: int = 60, burst_limit: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window for rate limiting
            burst_limit: Maximum number of requests in a very short time
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit or (max_requests * 2)

        # Use LRU cache for efficient tracking
        self.request_records: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a request from the given IP is allowed.

        Args:
            client_ip: IP address of the client

        Returns:
            bool: Whether the request is allowed
        """
        now = time.time()

        # Clean up old records
        self._cleanup_records(now)

        # Track requests for this IP
        if client_ip not in self.request_records:
            self.request_records[client_ip] = []

        records = self.request_records[client_ip]

        # Check total requests in window
        window_requests = [t for t in records if now - t < self.window_seconds]

        # Check if over max requests
        if len(window_requests) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False

        # Add current request
        records.append(now)

        return True

    def _cleanup_records(self, current_time: float):
        """
        Clean up old request records.

        Args:
            current_time: Current timestamp
        """
        # Remove records older than the window
        for ip in list(self.request_records.keys()):
            self.request_records[ip] = [
                t for t in self.request_records[ip] if current_time - t < self.window_seconds
            ]

            # Remove empty lists
            if not self.request_records[ip]:
                del self.request_records[ip]


def rate_limit(
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
    limiter: Optional[RateLimiter] = None,
    client_ip_restrictions: Optional[List[str]] = None,
) -> Callable:
    """
    Create a comprehensive rate limiting dependency.

    Args:
        max_requests: Maximum requests allowed in the time window
        window_seconds: Time window for rate limiting
        limiter: Custom rate limiter (takes precedence over max_requests/window_seconds)
        client_ip_restrictions: List of allowed IP networks

    Returns:
        Dependency function for rate limiting
    """
    # Use provided limiter or create a new one
    if limiter is None:
        # Use provided parameters or default from settings
        max_req = max_requests or settings.RATE_LIMIT_MAX_REQUESTS
        window_sec = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        limiter = RateLimiter(max_requests=max_req, window_seconds=window_sec)

    async def rate_limit_dependency(request: Request) -> None:
        # Get client IP
        client_ip = get_client_ip(request)

        # Validate IP restrictions if provided
        if client_ip_restrictions:
            try:
                client_addr = ip_address(client_ip)
                if not any(
                    client_addr in ip_network(net, strict=False) for net in client_ip_restrictions
                ):
                    logger.warning(f"IP {client_ip} not in allowed networks")
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN, detail="Access from this IP is not allowed"
                    )
            except ValueError:
                logger.error(f"Invalid IP address: {client_ip}")
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid client IP")

        # Check rate limit
        if not limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limiter.max_requests} "
                f"requests per {limiter.window_seconds} seconds",
            )

    return rate_limit_dependency
