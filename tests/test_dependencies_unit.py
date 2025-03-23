"""
Unit tests for API dependencies.

This module tests the dependency functions used by FastAPI endpoints
to ensure they provide the correct instances and handle errors appropriately.
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import Request, BackgroundTasks, HTTPException
from typing import Dict, Any, Generator

from app.api.dependencies import (
    get_enhanced_image_service,
    get_standard_image_service,
    get_storage_service,
    get_standard_rate_limit,
    get_heavy_rate_limit,
    get_api_key_dependency,
    log_request_info,
    set_api_version,
    set_v1_api_version,
    get_background_tasks,
    cleanup_temp_files
)
from app.core.service_provider import ServiceProvider
from app.services.image_service import BaseImageService
from app.services.storage_service import StorageService


class TestServiceDependencies:
    """Tests for service-providing dependencies."""
    
    @pytest.fixture
    def mock_service_provider(self):
        """Create a mock service provider."""
        with patch('app.core.services_setup.get_service_provider') as mock_get_provider:
            mock_provider = MagicMock(spec=ServiceProvider)
            mock_get_provider.return_value = mock_provider
            yield mock_provider
    
    def test_get_enhanced_image_service(self, mock_service_provider):
        """Test get_enhanced_image_service dependency."""
        # Set up mock
        mock_image_service = MagicMock(spec=BaseImageService)
        mock_service_provider.get.return_value = mock_image_service
        
        # Call the dependency
        result = get_enhanced_image_service()
        
        # Verify
        mock_service_provider.get.assert_called_once_with(BaseImageService, key="EnhancedImageService")
        assert result is mock_image_service
    
    def test_get_standard_image_service(self, mock_service_provider):
        """Test get_standard_image_service dependency."""
        # Set up mock
        mock_image_service = MagicMock(spec=BaseImageService)
        mock_service_provider.get.return_value = mock_image_service
        
        # Call the dependency
        result = get_standard_image_service()
        
        # Verify
        mock_service_provider.get.assert_called_once_with(BaseImageService, key="StandardImageService")
        assert result is mock_image_service
    
    def test_get_storage_service(self, mock_service_provider):
        """Test get_storage_service dependency."""
        # Set up mock
        mock_storage = MagicMock(spec=StorageService)
        mock_service_provider.get.return_value = mock_storage
        
        # Call the dependency
        result = get_storage_service()
        
        # Verify
        mock_service_provider.get.assert_called_once_with(StorageService)
        assert result is mock_storage


class TestRateLimitDependencies:
    """Tests for rate limiting dependencies."""
    
    def test_get_standard_rate_limit(self):
        """Test the standard rate limit dependency returns a callable."""
        with patch('app.api.dependencies.rate_limit') as mock_rate_limit:
            mock_limiter = MagicMock()
            mock_rate_limit.return_value = mock_limiter
            
            result = get_standard_rate_limit()
            
            assert mock_rate_limit.called
            assert result is mock_limiter
    
    def test_get_heavy_rate_limit(self):
        """Test the heavy rate limit dependency returns a callable with lower limits."""
        with patch('app.api.dependencies.rate_limit') as mock_rate_limit:
            mock_limiter = MagicMock()
            mock_rate_limit.return_value = mock_limiter
            
            result = get_heavy_rate_limit()
            
            mock_rate_limit.assert_called_with(max_requests=20, window_seconds=60)
            assert result is mock_limiter


class TestApiVersionDependencies:
    """Tests for API versioning dependencies."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        mock_req = MagicMock(spec=Request)
        mock_req.state = MagicMock()
        return mock_req
    
    def test_set_api_version(self, mock_request):
        """Test set_api_version correctly sets the version in request state."""
        # Call the dependency
        result = set_api_version(mock_request, "test_version")
        
        # Verify
        assert mock_request.state.api_version == "test_version"
        assert result is None  # Should return None
    
    def test_set_v1_api_version(self, mock_request):
        """Test set_v1_api_version calls set_api_version with v1."""
        # Use patch to mock the set_api_version function
        with patch('app.api.dependencies.set_api_version') as mock_set_version:
            mock_set_version.return_value = None
            
            # Call the dependency
            result = set_v1_api_version(mock_request)
            
            # Verify
            mock_set_version.assert_called_once_with(mock_request, "v1")
            assert result is None


class TestUtilityDependencies:
    """Tests for utility dependencies like logging and background tasks."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        mock_req = MagicMock(spec=Request)
        mock_req.client = MagicMock()
        mock_req.client.host = "127.0.0.1"
        mock_req.method = "GET"
        mock_req.url = MagicMock()
        mock_req.url.path = "/test/path"
        return mock_req
    
    @pytest.mark.asyncio
    async def test_log_request_info(self, mock_request):
        """Test log_request_info logs request info and returns start time."""
        with patch('app.api.dependencies.logger') as mock_logger:
            # Call the dependency
            start_time = await log_request_info(mock_request)
            
            # Verify
            assert isinstance(start_time, float)
            mock_logger.info.assert_called_once()
            assert "127.0.0.1" in mock_logger.info.call_args[0][0]
            assert "GET" in mock_logger.info.call_args[0][0]
            assert "/test/path" in mock_logger.info.call_args[0][0]
    
    def test_get_background_tasks(self):
        """Test get_background_tasks returns the passed background tasks."""
        mock_tasks = MagicMock(spec=BackgroundTasks)
        
        # Call the dependency
        result = get_background_tasks(mock_tasks)
        
        # Verify
        assert result is mock_tasks
    
    def test_cleanup_temp_files(self):
        """Test cleanup_temp_files logs the cleanup action."""
        with patch('app.api.dependencies.logger') as mock_logger:
            with patch('app.api.dependencies.get_storage_service') as mock_get_storage:
                mock_storage = MagicMock(spec=StorageService)
                mock_get_storage.return_value = mock_storage
                mock_storage.temp_dir = "/temp/dir"
                
                # Call the dependency
                cleanup_temp_files("test123")
                
                # Verify
                mock_logger.info.assert_called()
                assert "test123" in mock_logger.info.call_args_list[0][0][0]
                assert "Scheduling cleanup" in mock_logger.info.call_args_list[1][0][0]