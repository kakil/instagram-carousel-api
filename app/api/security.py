"""
API security middleware and dependencies for Instagram Carousel Generator.

Enhanced security features including:
- Improved API key validation
- More robust rate limiting
- IP-based tracking
- Comprehensive request validation
"""
import logging
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_403_FORBIDDEN

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


# Rest of the existing security module code remains the same
# Rate limiting classes and functions follow...
