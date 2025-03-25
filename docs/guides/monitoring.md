# Monitoring and Logging Guide

This guide explains how to use the monitoring and logging system in the Instagram Carousel Generator API. The API includes a comprehensive system for tracking performance, logging events, and collecting metrics.

## Table of Contents

1. [Logging Overview](#logging-overview)
2. [Performance Monitoring](#performance-monitoring)
3. [Metrics Collection](#metrics-collection)
4. [API Monitoring Dashboard](#api-monitoring-dashboard)
5. [Integration with External Tools](#integration-with-external-tools)
6. [Customizing Logging and Monitoring](#customizing-logging-and-monitoring)

## Logging Overview

The API uses a structured logging system that provides detailed information about API operations. Logs are output in a standardized format that makes them easy to parse and analyze.

### Log Levels

The following log levels are used:

- **DEBUG**: Detailed information, typically of interest only for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication that something unexpected happened, but the application is still working
- **ERROR**: Due to a more serious problem, the application might not be able to perform some functions
- **CRITICAL**: A serious error, indicating that the application may not be able to continue running

### Structured JSON Logging

In production, logs are formatted as JSON objects for better parsing by log aggregation tools. Each log entry includes:

- **timestamp**: ISO-formatted timestamp
- **level**: Log level
- **message**: Log message
- **logger**: Logger name
- **module**: Module name
- **function**: Function name
- **line**: Line number
- **hostname**: Server hostname
- **environment**: Production or development
- **request_id**: Unique ID for the request (when available)
- **additional context**: Operation-specific data

### Request Logging

Each API request is logged with:

- Start and end times
- Request method and path
- Response status code
- Processing time
- Client IP and user agent
- Any errors that occurred

### How to Use Logging

To log events in your code, import the appropriate logger:

```python
import logging

# Get a logger for the current module
logger = logging.getLogger(__name__)

# For general logging
logger.info("Operation completed successfully")
logger.error("An error occurred", exc_info=True)

# For request-specific logging
from app.core.logging import get_request_logger

request_logger = get_request_logger(request_id)
request_logger.info("Processing request", extra={"key": "value"})
```

### Log Configuration

Logging can be configured using environment variables:

- `LOG_LEVEL`: Set the minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `ENABLE_FILE_LOGGING`: Enable logging to files
- `LOG_FORMAT_JSON`: Format logs as JSON (recommended for production)
- `LOG_DIR`: Directory for log files
- `LOG_ROTATION_TYPE`: Type of log rotation (size or time)
- `LOG_MAX_SIZE`: Maximum log file size for size-based rotation
- `LOG_ROTATION_WHEN`: When to rotate logs for time-based rotation (D=daily, H=hourly)
- `LOG_ROTATION_INTERVAL`: Interval for time-based rotation
- `LOG_BACKUP_COUNT`: Number of backup log files to keep

## Performance Monitoring

The API includes tools for monitoring the performance of various operations.

### Context Manager

Use the context manager to monitor the performance of code blocks:

```python
from app.core.monitoring import monitor_performance_context

with monitor_performance_context(
    "operation_name",
    extra_param="value"
):
    # Your code here
    process_data()
```

### Decorators

For monitoring function performance, use decorators:

```python
from app.core.monitoring import monitor_performance, monitor_performance_async

# For synchronous functions
@monitor_performance("custom_operation_name")
def process_data():
    # Function implementation

# For asynchronous functions
@monitor_performance_async("custom_operation_name")
async def process_data_async():
    # Async function implementation
```

## Metrics Collection

The API automatically collects metrics about various operations:

### Request Metrics

- Total requests
- Successful requests
- Failed requests
- Average response time
- Response time by endpoint
- Error rate

### Carousel Generation Metrics

- Number of carousels generated
- Average generation time
- Success rate

### System Metrics

- CPU usage
- Memory usage
- Disk usage
- Uptime

### Custom Metrics

You can collect custom metrics using the metrics logger:

```python
from app.core.logging import metrics_logger

# Log a custom event
metrics_logger.log_request(
    request_id="unique_id",
    method="GET",
    path="/api/custom",
    status_code=200,
    duration_ms=150.5,
    user_agent="Custom Client",
    ip_address="127.0.0.1"
)

# Log carousel generation
metrics_logger.log_carousel_generation(
    carousel_id="abc123",
    num_slides=5,
    duration_ms=1250.75,
    success=True,
    error=None
)

# Log image processing
metrics_logger.log_image_processing(
    operation="resize",
    image_size=(1080, 1080),
    duration_ms=75.2,
    success=True
)
```

### Accessing Metrics

Metrics are available through the `/metrics` endpoint, which returns a JSON object with current metrics.

## API Monitoring Dashboard

The API includes a built-in monitoring dashboard that visualizes metrics:

### Accessing the Dashboard

Open the dashboard by navigating to: `/static/monitoring/dashboard.html`

### Dashboard Features

The dashboard shows:

- System health (CPU, memory, disk usage)
- Request statistics (total, successful, errors)
- Carousel generation metrics
- API health and error rate
- Response time trends
- Request volume by endpoint
- Endpoint performance details

The dashboard automatically refreshes every minute, but you can manually refresh at any time.

## Integration with External Tools

The logging and monitoring system is designed to integrate easily with external tools.

### Prometheus Integration

To expose metrics in Prometheus format, add the following endpoint:

```python
@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Get Prometheus-formatted metrics."""
    from app.api.monitoring import get_prometheus_metrics

    content = get_prometheus_metrics()
    return Response(content=content, media_type="text/plain")
```

### ELK Stack Integration

To forward logs to Elasticsearch:

1. Install the Elasticsearch Python client:
   ```
   pip install elasticsearch
   ```

2. Add an Elasticsearch handler to your logging configuration

### Datadog Integration

To send metrics to Datadog:

1. Install the Datadog Python client:
   ```
   pip install datadog
   ```

2. Configure the Datadog client in your application

## Customizing Logging and Monitoring

### Adding Custom Log Handlers

You can add custom log handlers by extending the logging configuration:

```python
import logging
from app.core.logging import configure_logging

# Configure base logging
configure_logging()

# Add custom handler
custom_handler = logging.StreamHandler()
custom_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(custom_handler)
```

### Extending Metrics Collection

To add custom metrics categories:

1. Add methods to the `MetricsLogger` class in `app/core/logging.py`
2. Update the `APIMetricsTracker` class in `app/api/monitoring.py`
3. Add visualizations to the dashboard in `app/static/monitoring/dashboard.html`

### Creating Custom Dashboards

You can create custom dashboards using any web-based visualization library:

1. Fetch metrics from the `/metrics` endpoint
2. Process and visualize the data
3. Deploy the dashboard to your preferred hosting platform

## Best Practices

1. **Use unique request IDs**: Always use unique request IDs for better traceability
2. **Log appropriate levels**: Use appropriate log levels for different types of events
3. **Include context**: Add relevant context to log messages
4. **Monitor performance**: Use monitoring tools for performance-critical operations
5. **Set appropriate log rotation**: Configure log rotation to avoid disk space issues
6. **Review logs regularly**: Regularly review logs to identify issues early
7. **Set up alerts**: Configure alerts for critical errors and performance issues

## Troubleshooting

### Common Issues

1. **High log volume**: Adjust the log level to reduce volume in production
2. **Missing context in logs**: Ensure you're using `extra` parameter with your log calls
3. **Performance impact**: Reduce logging detail if performance is impacted

### Getting Help

If you encounter issues with the logging or monitoring system, check:

1. The app logs for error messages
2. The configuration in `.env` or environment variables
3. The API endpoints for debugging information
