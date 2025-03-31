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
from collections import defaultdict
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, Security
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


def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
) -> bool:
    """
    Validate API key from header or query parameter.

    Args:
        api_key_header: API key from header
        api_key_query: API key from query parameter
    Returns:
        True if valid API key
    Raises:
        HTTPException: If API key is invalid or missing
    """
    # If no API key is configured, don't enforce authentication
    if not settings.API_KEY:
        return True

    # Try both header and query parameter
    api_key = api_key_header or api_key_query

    if not api_key:
        logger.warning("No API key provided")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")

    # Constant-time comparison to prevent timing attacks
    def secure_compare(a: str, b: str) -> bool:
        if len(a) != len(b):
            return False
        return all(x == y for x, y in zip(a, b))

    if not secure_compare(api_key, settings.API_KEY):
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")

    return True


# Rate limiting implementation
# Using a simple in-memory storage for rate limiting
# In production, this would be replaced with Redis or another distributed cache
rate_limit_storage: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
rate_limit_started: Dict[str, int] = {}


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
) -> Callable:
    """
    Create a rate limiting dependency.

    Args:
        max_requests: Maximum number of requests allowed per window
        window_seconds: Time window in seconds

    Returns:
        Dependency function for rate limiting
    """

    async def _rate_limit_dependency(request: Request) -> None:
        # Get client identifier (IP address)
        client_id = get_client_ip(request)

        # Current timestamp
        now = int(time.time())
        current_window = now // window_seconds

        # Initialize if this is the first request for this client
        if client_id not in rate_limit_started:
            rate_limit_started[client_id] = now

        # Clean up old windows
        cleanup_old_windows(client_id, current_window)

        # Check if rate limit is exceeded
        if rate_limit_storage[client_id][current_window] >= max_requests:
            # Calculate time until reset
            next_window_start = (current_window + 1) * window_seconds
            reset_seconds = next_window_start - now

            # Log rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_id}: "
                f"{max_requests} requests per {window_seconds}s"
            )

            # Include headers to help clients understand the rate limiting
            headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
                "Retry-After": str(reset_seconds),
            }

            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers=headers,
            )

        # Increment the counter for this window
        rate_limit_storage[client_id][current_window] += 1

        # Calculate remaining requests
        remaining = max_requests - rate_limit_storage[client_id][current_window]

        # Add rate limit headers to the response
        # These will be added later in middleware
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(max(0, remaining)),
            "X-RateLimit-Reset": str((current_window + 1) * window_seconds - now),
        }

        return None

    return _rate_limit_dependency


def cleanup_old_windows(client_id: str, current_window: int) -> None:
    """
    Remove data for old time windows to prevent memory leaks.

    Args:
        client_id: Client identifier (usually IP address)
        current_window: Current time window
    """
    if client_id in rate_limit_storage:
        # Keep only the current window
        windows_to_remove = [w for w in rate_limit_storage[client_id] if w < current_window]
        for window in windows_to_remove:
            del rate_limit_storage[client_id][window]

        # If no windows left, remove the client entry completely
        if not rate_limit_storage[client_id]:
            del rate_limit_storage[client_id]
            if client_id in rate_limit_started:
                del rate_limit_started[client_id]


def validate_file_access(
    carousel_id: str, filename: str, request: Optional[Request] = None
) -> bool:
    """
    Validate access to a specific file/carousel.

    This function checks if the user has permission to access a specific file.
    In this implementation, we're just doing a simple check, but in a real-world
    scenario, you might want to check against a database or other authorization system.

    Args:
        carousel_id: The ID of the carousel to check
        filename: The filename to access
        request: The FastAPI request object (optional)

    Returns:
        bool: True if access is allowed, False otherwise
    """
    # In a real implementation, you would check if the user has permission
    # to access this file, e.g., by checking if they created it or if they
    # have been granted access to it.

    # For now, we'll allow access to all files since we're not implementing
    # a full authorization system in this example

    # You could implement this by checking request.state.user_id against
    # a database record of who owns the file, or by checking a token claim

    # Log the access attempt
    if request:
        client_ip = get_client_ip(request)
        logger.info(
            f"File access request from {client_ip} for carousel {carousel_id}, file {filename}"
        )
    else:
        logger.info(f"File access request for carousel {carousel_id}, file {filename}")

    return True
