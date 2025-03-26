#!/bin/bash

# Create necessary directories with .gitkeep files to ensure they're tracked in git
mkdir -p static/temp
mkdir -p static/assets
touch static/temp/.gitkeep
touch static/assets/.gitkeep

# Create a scripts directory if it doesn't exist
mkdir -p scripts

# Make the docker.sh script executable
chmod +x scripts/docker.sh

# Create logs directory for development
mkdir -p logs
touch logs/.gitkeep

echo "Folder structure created successfully"
