# API Versioning Guide

## Overview

The Instagram Carousel Generator API uses a robust versioning system to ensure backward compatibility while allowing for improvements and new features. This document explains our versioning strategy and how to work with different API versions.

## Versioning Strategy

Our API follows semantic versioning with the following principles:

1. **URL-based versioning**: All API endpoints include the version in the URL path (e.g., `/api/v1/generate-carousel`)
2. **Backwards compatibility**: Within a major version, we maintain backwards compatibility
3. **Deprecation period**: When a version is deprecated, we provide at least 6 months notice before removing it
4. **Clear communication**: We use HTTP headers to notify you about versioning changes

## Current Versions

| Version | Status | Released | Deprecated | Sunset Date |
|---------|--------|----------|------------|-------------|
| v1      | Current | March 15, 2024 | N/A | N/A |

## How to Specify API Version

### In URLs

Always include the version in your API requests:

```
https://api.kitwanaakil.com/api/v1/generate-carousel
```

This ensures your integration continues to work even when new versions are released.

## Version Lifecycle

Each API version goes through the following lifecycle:

1. **Current**: The newest, recommended version
2. **Supported**: Still fully supported but no longer the newest version
3. **Deprecated**: Still works but scheduled for removal (notice via HTTP headers)
4. **Sunset**: No longer available

## Deprecation Notices

When using a deprecated version, you'll receive the following HTTP headers:

- `Deprecation: YYYY-MM-DD` - The date the version was deprecated
- `Sunset: YYYY-MM-DD` - The date the version will be removed
- `Link: </docs#tag/v2-endpoints>; rel="alternate"; title="Latest API version"` - Link to the latest version

## Migration Between Versions

When it's time to migrate to a new version, we'll provide:

1. Migration guides with specific changes
2. Examples of updated request/response formats
3. Coexistence support during the transition period

## Best Practices

1. **Always specify version in URLs**: Don't rely on defaults
2. **Watch for deprecation headers**: Check for and log deprecation notices in your integration
3. **Plan migrations early**: Start testing with new versions as soon as they're announced
4. **Use the version compatibility endpoints**: Check your payloads for compatibility

## Version Compatibility Endpoint

To check if your requests are compatible with newer API versions, use:

```
POST /api/v1/check-compatibility
```

This accepts your current v1 request format and tells you if it's compatible with newer versions.

## Notification of Changes

To stay informed about API versioning changes:

1. Subscribe to our developer newsletter
2. Monitor the API changelog
3. Follow our GitHub repository

## FAQ

### What happens if I don't specify a version?

Without a version specified, the request will fail with a 404 error. Always include the version in your API requests.

### How long will deprecated versions be available?

We maintain deprecated versions for at least 6 months after deprecation notice, giving you time to migrate.

### Can I use multiple API versions simultaneously?

Yes, you can make calls to different versions simultaneously during your migration process.

### Will minor updates within a version break my integration?

No, we maintain backward compatibility within a major version. Minor updates only add new features or optional parameters.