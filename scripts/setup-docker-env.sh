#!/bin/bash

# Instagram Carousel Generator Docker Environment Setup Script
# This script sets up the necessary folder structure and files for Docker development

set -e

# Define colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Docker development environment for Instagram Carousel Generator...${NC}"

# Create necessary directories
echo -e "${GREEN}Creating directory structure...${NC}"
mkdir -p static/temp
mkdir -p static/assets
mkdir -p docker/nginx
mkdir -p .devcontainer
mkdir -p scripts
mkdir -p logs

# Create .gitkeep files to ensure empty directories are tracked in git
touch static/temp/.gitkeep
touch static/assets/.gitkeep
touch logs/.gitkeep

# Make sure the Docker utility script is executable
chmod +x scripts/docker.sh

# Check if the Nginx configuration file exists, create if not
if [ ! -f docker/nginx/default.conf ]; then
    echo -e "${GREEN}Creating Nginx configuration file...${NC}"
    cat > docker/nginx/default.conf << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://api:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for development hot-reloading
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Serve static files directly
    location /static/ {
        alias /app/static/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Health check
    location = /health {
        proxy_pass http://api:5001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Add cache headers to prevent caching of health check
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
EOF
fi

# Create a sample .env file if it doesn't exist
if [ ! -f .env.example ]; then
    echo -e "${GREEN}Creating sample .env.example file...${NC}"
    cat > .env.example << 'EOF'
# API Settings
API_PREFIX=/api
API_VERSION=v1
DEBUG=True
API_KEY=your_development_api_key

# Server Settings
HOST=0.0.0.0
PORT=5001
PRODUCTION=False

# Public Access Settings
PUBLIC_BASE_URL=http://localhost

# Path Settings
TEMP_DIR=/app/static/temp

# Image Settings
DEFAULT_WIDTH=1080
DEFAULT_HEIGHT=1080
DEFAULT_BG_COLOR_R=18
DEFAULT_BG_COLOR_G=18
DEFAULT_BG_COLOR_B=18

# Storage Settings
TEMP_FILE_LIFETIME_HOURS=24

# CORS Settings
ALLOW_ORIGINS=*

# Rate Limiting Settings
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
EOF
fi

echo -e "${GREEN}Docker environment setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Run the development environment:"
echo "   ./scripts/docker.sh dev"
echo ""
echo "2. Access the API at: http://localhost:5001"
echo "3. Access the documentation at: http://localhost:8080"
echo "4. Access the API docs at: http://localhost:5001/docs"
echo ""
echo -e "${YELLOW}For more information, see the README.md file.${NC}"
