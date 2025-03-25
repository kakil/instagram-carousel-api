"""
API security middleware and dependencies for Instagram Carousel Generator.

This module provides security-related middleware and dependencies for FastAPI,
including API key authentication, rate limiting, and request validation.
"""
import logging
import re
import time
from typing import Callable, Dict, List

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

# Rate limiting storage (in-memory for simplicity)
# In production, you would use Redis or similar for distributed systems
# Format: {ip_address: [(timestamp1), (timestamp2), ...]}
request_records: Dict[str, List[float]] = {}


def get_api_key(
    api_key_header: str = Security(api_key_header),
    api_key_query: str = Security(api_key_query),
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
    # This helps in development/testing
    if not settings.API_KEY:
        return True
    # Try to get API key from header or query parameter
    api_key = api_key_header or api_key_query
    if api_key == settings.API_KEY:
        return True
    logger.warning(f"Invalid API key attempt: {api_key_header or api_key_query}")
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")


def rate_limit(max_requests: int = 100, window_seconds: int = 60) -> Callable:
    """
    Create a rate limiting dependency.

    Args:
        max_requests: Maximum number of requests allowed in the time window
        window_seconds: Time window in seconds
    Returns:
        A dependency function for rate limiting
    """

    async def rate_limit_dependency(request: Request) -> None:
        # Get client IP
        client_host = request.client.host if request.client else "unknown"

        # Get current time
        now = time.time()

        # Initialize record for this client
        if client_host not in request_records:
            request_records[client_host] = []

        # Clean up old records
        request_records[client_host] = [
            timestamp
            for timestamp in request_records[client_host]
            if now - timestamp < window_seconds
        ]

        # Check if rate limit is exceeded
        if len(request_records[client_host]) >= max_requests:
            logger.warning(f"Rate limit exceeded for client: {client_host}")
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds",
            )

        # Add current request timestamp
        request_records[client_host].append(now)

        # Cleanup old IPs periodically (every 100 requests)
        if sum(len(records) for records in request_records.values()) % 100 == 0:
            cleanup_old_rate_records(now, window_seconds)

    return rate_limit_dependency


def cleanup_old_rate_records(now: float, window_seconds: int) -> None:
    """
    Clean up old rate limiting records.

    Args:
        now: Current timestamp
        window_seconds: Time window in seconds
    """
    ips_to_remove = []

    for ip, timestamps in request_records.items():
        # Keep only records within the time window
        valid_timestamps = [ts for ts in timestamps if now - ts < window_seconds]

        if valid_timestamps:
            request_records[ip] = valid_timestamps
        else:
            ips_to_remove.append(ip)

    # Remove empty IP records
    for ip in ips_to_remove:
        del request_records[ip]


def validate_file_access(carousel_id: str, filename: str) -> None:
    """
    Validate file access to prevent directory traversal.

    Args:
        carousel_id: Unique identifier for the carousel
        filename: Name of the file to access

    Raises:
        HTTPException: If validation fails
    """
    # Validate carousel_id format (alphanumeric only)
    if not re.match(r"^[a-zA-Z0-9-_]+$", carousel_id):
        logger.warning(f"Invalid carousel_id format: {carousel_id}")
        raise HTTPException(status_code=404, detail="Invalid carousel ID format")

    # Validate filename format (prevent path traversal)
    if not re.match(r"^[a-zA-Z0-9-_]+\.[a-zA-Z0-9]+$", filename):
        logger.warning(f"Invalid filename format: {filename}")
        raise HTTPException(status_code=404, detail="Invalid filename format")

    # Ensure filename doesn't contain path traversal attempts
    if ".." in filename or "/" in filename:
        logger.warning(f"Path traversal attempt detected: {filename}")
        raise HTTPException(status_code=403, detail="Invalid file access")
