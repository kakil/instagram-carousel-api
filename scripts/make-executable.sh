#!/bin/bash

# Make all shell scripts executable
# This is useful after cloning the repository

# Define colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Making all shell scripts executable...${NC}"

# Find all shell scripts and make them executable
find . -type f -name "*.sh" | while read file; do
    chmod +x "$file"
    echo -e "${GREEN}Made executable: ${NC}$file"
done

# Make Docker health check script executable
if [ -f "docker/healthcheck.sh" ]; then
    chmod +x docker/healthcheck.sh
    echo -e "${GREEN}Made executable: ${NC}docker/healthcheck.sh"
fi

echo -e "${BLUE}Done!${NC}"
