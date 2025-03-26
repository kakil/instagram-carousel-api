#!/bin/bash
set -e

# Simple health check script for Docker
# Returns 0 if the API is healthy, 1 otherwise

HOST="localhost"
PORT="5001"
ENDPOINT="/health"
TIMEOUT=5

# Try to connect to the health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "http://$HOST:$PORT$ENDPOINT")

# Check if the response is 200 OK
if [ "$response" -eq 200 ]; then
    echo "API is healthy (HTTP $response)"
    exit 0
else
    echo "API is unhealthy (HTTP $response)"
    exit 1
fi
