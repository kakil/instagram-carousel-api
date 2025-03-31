"""
Monitoring endpoints for the Instagram Carousel Generator API.

This module provides endpoints for accessing monitoring data,
including metrics, health status, and the monitoring dashboard.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import psutil
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from app.api.security import get_api_key
from app.core.config import settings
from app.services.storage_service import StorageService

# Set up router
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Set up logging
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard(request: Request):
    """
    Get HTML monitoring dashboard.

    Returns:
        HTML dashboard page
    """
    try:
        # Log dashboard request
        logger.info("Monitoring dashboard requested")

        # Determine the path to the dashboard HTML
        dashboard_path = settings.BASE_DIR / "static" / "monitoring" / "dashboard.html"

        # Check if file exists
        if not dashboard_path.exists():
            logger.error(f"Dashboard file not found at {dashboard_path}")
            raise HTTPException(status_code=404, detail="Dashboard file not found")

        # Read the file content
        with open(dashboard_path, "r") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving monitoring dashboard: {str(e)}")


@router.get("/metrics")
async def get_api_metrics(request: Request):
    """
    Get API metrics.

    Returns:
        JSON with API metrics
    """
    try:
        # Log metrics request
        logger.info("API metrics requested")

        # Check if monitoring is enabled
        if not settings.ENABLE_MONITORING:
            return {
                "status": "disabled",
                "message": "Monitoring is disabled. Set ENABLE_MONITORING=True to enable.",
                "timestamp": datetime.now().isoformat(),
            }

        # Get uptime
        process = psutil.Process(os.getpid())
        uptime = time.time() - process.create_time()

        # Get system metrics if enabled
        system_metrics = {}
        if settings.ENABLE_SYSTEM_METRICS:
            system_metrics = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            }

        # Get carousel count
        carousel_count = count_carousels()

        # Create basic metrics
        metrics_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "api_version": "v1",
            "uptime": uptime,
            "system": system_metrics,
            "carousels": {
                "count": carousel_count,
            },
            "requests": {
                "total": 0,  # Placeholder for actual metrics
                "successful": 0,
                "errors": 0,
                "error_rate": 0,
            },
            "endpoints": {},  # Placeholder for endpoint metrics
        }

        return metrics_data
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        return {
            "status": "error",
            "message": "Failed to generate metrics",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


@router.get("/metrics/detailed")
async def get_detailed_metrics(
    request: Request, _: bool = Depends(get_api_key)  # Require API key for detailed metrics
):
    """
    Get detailed API metrics.

    This endpoint returns comprehensive metrics about API usage,
    performance, and system status. It requires API key authentication.

    Returns:
        Detailed metrics data
    """
    try:
        # Log metrics request
        logger.info("Detailed metrics requested")

        # Check if monitoring is enabled
        if not settings.ENABLE_MONITORING:
            return {
                "status": "disabled",
                "message": "Monitoring is disabled. Set ENABLE_MONITORING=True to enable.",
                "timestamp": datetime.now().isoformat(),
            }

        # Get basic metrics (same as regular metrics endpoint)
        metrics_data = await get_api_metrics(request)

        # Add system metrics if enabled
        if settings.ENABLE_SYSTEM_METRICS:
            metrics_data["system"] = {
                "cpu": {
                    "usage_percent": psutil.cpu_percent(),
                    "count": psutil.cpu_count(),
                    "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
                "network": {
                    "connections": len(psutil.net_connections()),
                },
                "process": {
                    "pid": os.getpid(),
                    "creation_time": psutil.Process(os.getpid()).create_time(),
                    "cpu_percent": psutil.Process(os.getpid()).cpu_percent(),
                    "memory_percent": psutil.Process(os.getpid()).memory_percent(),
                    "threads": len(psutil.Process(os.getpid()).threads()),
                },
            }

        # Add timestamp
        metrics_data["timestamp"] = datetime.now().isoformat()

        return metrics_data
    except Exception as e:
        logger.error(f"Error generating detailed metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating detailed metrics: {str(e)}")


@router.get("/metrics/prometheus")
async def prometheus_metrics(request: Request):
    """
    Get metrics in Prometheus format.

    Returns:
        Prometheus-formatted metrics
    """
    try:
        # Log metrics request
        logger.info("Prometheus metrics requested")

        # Check if monitoring is enabled
        if not settings.ENABLE_MONITORING:
            return Response(
                content="# Monitoring is disabled. Set ENABLE_MONITORING=True to enable.",
                media_type="text/plain",
            )

        # Get metrics
        metrics_data = await get_api_metrics(request)

        # Convert to Prometheus format
        prometheus_lines = []

        # Add API metrics
        requests = metrics_data.get("requests", {})
        prometheus_lines.append("# HELP api_requests_total Total number of API requests")
        prometheus_lines.append("# TYPE api_requests_total counter")
        # B113 warning is not applicable here as this is string formatting, not a request
        prometheus_lines.append(f"api_requests_total {requests.get('total', 0)}")  # nosec

        prometheus_lines.append(
            "# HELP api_request_errors_total Total number of API request errors"
        )
        prometheus_lines.append("# TYPE api_request_errors_total counter")
        # B113 warning is not applicable here as this is string formatting, not a request
        prometheus_lines.append(f"api_request_errors_total {requests.get('errors', 0)}")  # nosec

        prometheus_lines.append(
            "# HELP api_request_duration_milliseconds Average API request duration in milliseconds"
        )
        prometheus_lines.append("# TYPE api_request_duration_milliseconds gauge")
        # B113 warning is not applicable here as this is string formatting, not a request
        prometheus_lines.append(
            f"api_request_duration_milliseconds {requests.get('avg_response_time_ms', 0)}"  # nosec
        )

        # Add carousel metrics
        carousels = metrics_data.get("carousels", {})
        prometheus_lines.append(
            "# HELP carousel_generation_total Total number of carousels generated"
        )
        prometheus_lines.append("# TYPE carousel_generation_total counter")
        prometheus_lines.append(f"carousel_generation_total {carousels.get('total_generated', 0)}")

        prometheus_lines.append(
            "# HELP carousel_generation_duration_milliseconds Average carousel generation "
            "duration in milliseconds"
        )
        prometheus_lines.append("# TYPE carousel_generation_duration_milliseconds gauge")
        prometheus_lines.append(
            "carousel_generation_duration_milliseconds "
            f"{carousels.get('avg_generation_time_ms', 0)}"
        )

        # Add system metrics if enabled
        if settings.ENABLE_SYSTEM_METRICS:
            system = metrics_data.get("system", {})
            prometheus_lines.append("# HELP system_cpu_usage CPU usage percentage")
            prometheus_lines.append("# TYPE system_cpu_usage gauge")
            prometheus_lines.append(f"system_cpu_usage {system.get('cpu_usage', 0)}")

            prometheus_lines.append("# HELP system_memory_usage Memory usage percentage")
            prometheus_lines.append("# TYPE system_memory_usage gauge")
            prometheus_lines.append(f"system_memory_usage {system.get('memory_usage', 0)}")

            prometheus_lines.append("# HELP system_disk_usage Disk usage percentage")
            prometheus_lines.append("# TYPE system_disk_usage gauge")
            prometheus_lines.append(f"system_disk_usage {system.get('disk_usage', 0)}")

        # Add uptime metric
        prometheus_lines.append("# HELP api_uptime_seconds API uptime in seconds")
        prometheus_lines.append("# TYPE api_uptime_seconds counter")
        prometheus_lines.append(f"api_uptime_seconds {metrics_data.get('uptime', 0)}")

        # Join all lines with newlines
        prometheus_content = "\n".join(prometheus_lines)

        return Response(content=prometheus_content, media_type="text/plain")
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {str(e)}")
        return Response(content=f"# Error generating metrics: {str(e)}", media_type="text/plain")


@router.get("/logs/summary")
async def get_log_summary(
    hours: int = 24, level: str = "ERROR", _: bool = Depends(get_api_key)  # Require API key
):
    """
    Get a summary of recent log entries.

    Args:
        hours: Number of hours to look back
        level: Minimum log level to include

    Returns:
        Summary of log entries
    """
    try:
        # Check if monitoring is enabled
        if not settings.ENABLE_MONITORING:
            return {
                "status": "disabled",
                "message": "Monitoring is disabled. Set ENABLE_MONITORING=True to enable.",
                "timestamp": datetime.now().isoformat(),
            }

        # Get log directory
        log_dir = settings.LOG_DIR

        # Get log file path
        log_path = log_dir / f"{settings.PROJECT_NAME.lower().replace(' ', '_')}.log"

        if not log_path.exists():
            return {"status": "error", "message": "Log file not found"}

        # Parse logs and count by level and module
        log_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        module_counts = {}
        endpoint_counts = {}
        error_samples = []

        # Convert level to priority number
        level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

        min_priority = level_priority.get(level.upper(), 1)

        # Get current time
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)

        # Read the last 1000 lines for a quick summary (adjust as needed)
        with open(log_path, "r") as f:
            # Start from the end of the file
            f.seek(0, os.SEEK_END)
            file_size = f.tell()

            # Read the last portion of the file
            chunk_size = min(file_size, 100000)  # 100KB or file size, whichever is smaller
            f.seek(max(0, file_size - chunk_size), os.SEEK_SET)

            # Read lines
            lines = f.readlines()

            # Process each line
            for line in lines:
                try:
                    # Check if it's JSON format
                    if settings.LOG_FORMAT_JSON and line.strip().startswith("{"):
                        log_entry = json.loads(line)

                        # Check timestamp if available
                        if "timestamp" in log_entry:
                            try:
                                log_time = datetime.fromisoformat(log_entry["timestamp"])
                                if log_time < cutoff_time:
                                    continue
                            except (ValueError, TypeError):
                                pass

                        # Count by level
                        level = log_entry.get("level", "UNKNOWN")
                        if level in log_counts:
                            log_counts[level] += 1

                        # Check if we should include based on level priority
                        current_priority = level_priority.get(level, 0)
                        if current_priority < min_priority:
                            continue

                        # Count by module
                        module = log_entry.get("module", "unknown")
                        if module not in module_counts:
                            module_counts[module] = 0
                        module_counts[module] += 1

                        # Count by endpoint (for request logs)
                        extra = log_entry.get("extra", {})
                        if isinstance(extra, dict):
                            endpoint = extra.get("endpoint") or extra.get("path")
                            if endpoint:
                                if endpoint not in endpoint_counts:
                                    endpoint_counts[endpoint] = 0
                                endpoint_counts[endpoint] += 1

                        # Collect error samples
                        if level in ("ERROR", "CRITICAL") and len(error_samples) < 10:
                            error_samples.append(
                                {
                                    "timestamp": log_entry.get("timestamp"),
                                    "message": log_entry.get("message"),
                                    "module": module,
                                    "function": log_entry.get("function"),
                                    "line": log_entry.get("line"),
                                }
                            )
                    else:
                        # Simple text format parsing (less accurate)
                        parts = line.split(" - ")
                        if len(parts) >= 3:
                            # Try to extract level
                            for lvl in log_counts.keys():
                                if lvl in parts[1]:
                                    log_counts[lvl] += 1
                                    break
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Error generating log summary: {str(e)}")
                    # Skip non-JSON lines or malformed entries
                    continue

        return {
            "status": "success",
            "period": f"Last {hours} hours",
            "log_counts": log_counts,
            "module_counts": module_counts,
            "endpoint_counts": endpoint_counts,
            "error_samples": error_samples,
            "log_file": str(log_path),
        }
    except Exception as e:
        logger.error(f"Error generating log summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating log summary: {str(e)}")


@router.post("/events/carousel_generation")
async def log_carousel_generation_event(
    carousel_id: str,
    num_slides: int,
    duration_ms: float,
    success: bool,
    error: Optional[str] = None,
    _: bool = Depends(get_api_key),  # Require API key
):
    """
    Log a carousel generation event for metrics tracking.

    Args:
        carousel_id: Unique carousel ID
        num_slides: Number of slides generated
        duration_ms: Duration in milliseconds
        success: Whether generation was successful
        error: Error message if failed

    Returns:
        Success message
    """
    try:
        # Log the event
        logger.info(
            f"Carousel generation event: {carousel_id} - {num_slides} slides - {success}",
            extra={
                "carousel_id": carousel_id,
                "num_slides": num_slides,
                "duration_ms": duration_ms,
                "success": success,
                "error": error,
            },
        )

        return {"status": "success", "message": "Event logged successfully"}
    except Exception as e:
        logger.error(f"Error logging carousel generation event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging event: {str(e)}")


def count_carousels(storage_service: Optional[StorageService] = None) -> int:
    """
    Count the number of carousel directories in the temp directory.

    Args:
        storage_service: Optional StorageService instance

    Returns:
        Number of carousel directories
    """
    try:
        # Get storage service if not provided
        if storage_service is None:
            # Create a new service instance
            storage_service = StorageService()

        # Get the temp directory
        temp_dir = storage_service.temp_dir

        # Count directories that look like carousel IDs (excluding hidden directories)
        count = sum(
            1
            for item in os.listdir(temp_dir)
            if os.path.isdir(os.path.join(temp_dir, item)) and not item.startswith(".")
        )

        return count
    except Exception as e:
        logger.error(f"Error counting carousels: {str(e)}")
        return 0
