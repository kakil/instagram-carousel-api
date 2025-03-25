"""
Middleware for API versioning in the Instagram Carousel Generator.

This module provides middleware for managing API version compatibility,
including version deprecation notices and compatibility warnings.
"""
import logging
import re
from datetime import date
from typing import Awaitable, Callable, Dict, List, Optional

from fastapi import Request

# Configure logging
logger = logging.getLogger(__name__)

# API version information
VERSION_INFO = {
    "v1": {
        "introduced": date(2024, 3, 15),
        "deprecated": None,  # Not deprecated yet
        "sunset": None,  # No sunset date yet
        "latest": True,  # Currently the latest version
    },
    # Add future versions here
    # "v2": {
    #     "introduced": date(2025, 1, 1),
    #     "deprecated": None,
    #     "sunset": None,
    #     "latest": True,  # Would become the latest
    # },
}


# When adding v2, update v1 to:
# "v1": {
#     "introduced": date(2024, 3, 15),
#     "deprecated": date(2025, 1, 1),  # Deprecated when v2 is introduced
#     "sunset": date(2025, 7, 1),      # Will be removed 6 months after deprecation
#     "latest": False,                 # No longer the latest
# },


async def version_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    """
    Middleware to handle API version deprecation and sunset notices.

    Args:
        request: FastAPI request object
        call_next: Next middleware or endpoint handler

    Returns:
        Response from the next middleware or endpoint handler
    """
    # Extract version from path if possible using regex
    version_pattern = r"/api/(?P<version>v\d+)/"
    match = re.search(version_pattern, request.url.path)

    if match:
        version = match.group("version")

        # Check if this version exists in our VERSION_INFO
        if version in VERSION_INFO:
            response = await call_next(request)

            version_data = VERSION_INFO[version]

            # Add deprecation header if version is deprecated
            if version_data.get("deprecated"):
                # Format according to RFC 8594
                sunset_date = version_data.get("sunset")
                if sunset_date:
                    # Add Sunset header with the date of removal
                    response.headers["Sunset"] = sunset_date.isoformat()

                # Add deprecation notice
                response.headers["Deprecation"] = version_data["deprecated"].isoformat()

                # Add Link header with info about the latest version
                latest_version = next(
                    (v for v, info in VERSION_INFO.items() if info.get("latest")), None
                )

                if latest_version:
                    # Point to the documentation for the latest version
                    response.headers["Link"] = (
                        f"</docs#tag/{latest_version}-endpoints>; "
                        'rel="alternate"; '
                        'title="Latest API version"'
                    )

            # If this isn't the latest version but not yet deprecated,
            # add a suggestion header
            elif not version_data.get("latest"):
                latest_version = next(
                    (v for v, info in VERSION_INFO.items() if info.get("latest")), None
                )

                if latest_version:
                    response.headers["X-API-Suggest-Version"] = latest_version

            return response

    # If no version found in path or version not in our info, just pass through
    return await call_next(request)


def get_all_versions() -> List[Dict]:
    """
    Get information about all API versions for documentation.

    Returns:
        List of dictionaries with version information
    """
    versions = []

    for version, info in VERSION_INFO.items():
        version_data = {
            "version": version,
            "introduced": info["introduced"].isoformat(),
            "status": "current"
            if info.get("latest")
            else ("deprecated" if info.get("deprecated") else "supported"),
        }

        if info.get("deprecated"):
            version_data["deprecated"] = info["deprecated"].isoformat()

        if info.get("sunset"):
            version_data["sunset"] = info["sunset"].isoformat()

        versions.append(version_data)

    return versions


def get_latest_version() -> Optional[str]:
    """
    Get the latest API version.

    Returns:
        Latest version string or None if no latest version is defined
    """
    for version, info in VERSION_INFO.items():
        if info.get("latest"):
            return version

    return None
