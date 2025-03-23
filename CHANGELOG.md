# Changelog

All notable changes to the Instagram Carousel Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-03-23

### Added
- Initial release of Instagram Carousel Generator
- FastAPI-based API for generating Instagram carousel images
- Core image generation service with gradient text and proper text wrapping
- Service for temporary file storage and management
- Support for custom fonts and styling
- Comprehensive error handling and logging
- API versioning support
- Dependency injection system
- Security features including API key authentication and rate limiting
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite
- Docker support for development and production

### Changed
- Refactored from prototype implementation to a modular, maintainable architecture
- Enhanced text rendering with better Unicode support
- Improved error slides with more user-friendly information

### Fixed
- Unicode character rendering issues
- Temporary file cleanup reliability
- Path traversal security vulnerabilities