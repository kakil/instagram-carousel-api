#!/bin/bash

# Create necessary directory structure for Docker implementation
# This script ensures all required directories exist

# Define colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Creating directory structure for Docker implementation...${NC}"

# Create directories
mkdir -p docker/nginx
mkdir -p .devcontainer
mkdir -p scripts
mkdir -p static/temp
mkdir -p static/assets
mkdir -p docs/guides
mkdir -p logs

# Create .gitkeep files for empty directories
touch static/temp/.gitkeep
touch static/assets/.gitkeep
touch logs/.gitkeep

# Make sure scripts are executable
find ./scripts -name "*.sh" -exec chmod +x {} \;
find ./docker -name "*.sh" -exec chmod +x {} \;

echo -e "${GREEN}Directory structure created successfully!${NC}"
