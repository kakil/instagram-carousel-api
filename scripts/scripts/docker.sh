#!/bin/bash

# Docker utility script for Instagram Carousel Generator API
# Usage: ./scripts/docker.sh [command]

set -e

# Define colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function for displaying help message
function show_help {
    echo -e "${BLUE}Instagram Carousel Generator Docker Utility${NC}"
    echo ""
    echo "Usage: ./scripts/docker.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev             - Start development environment"
    echo "  dev:build       - Rebuild development environment"
    echo "  test            - Run tests in Docker"
    echo "  test:coverage   - Run tests with coverage report"
    echo "  prod            - Start production environment"
    echo "  prod:build      - Rebuild production environment"
    echo "  clean           - Clean Docker resources"
    echo "  logs            - Show logs"
    echo "  shell           - Open a shell in the API container"
    echo "  help            - Show this help message"
    echo ""
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    exit 1
fi

# Execute command based on the first argument
case "$1" in
    dev)
        echo -e "${GREEN}Starting development environment...${NC}"
        docker-compose up
        ;;
    dev:build)
        echo -e "${GREEN}Rebuilding and starting development environment...${NC}"
        docker-compose up --build
        ;;
    test)
        echo -e "${GREEN}Running tests in Docker...${NC}"
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        ;;
    test:coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit
        echo -e "${BLUE}Coverage report available in ./coverage_html/index.html${NC}"
        ;;
    prod)
        if [ ! -f .env ]; then
            echo -e "${YELLOW}Warning: .env file not found. Using default values for production.${NC}"
        fi
        echo -e "${GREEN}Starting production environment...${NC}"
        docker-compose -f docker-compose.prod.yml up -d
        echo -e "${GREEN}Production API is running at http://localhost:5001${NC}"
        ;;
    prod:build)
        if [ ! -f .env ]; then
            echo -e "${YELLOW}Warning: .env file not found. Using default values for production.${NC}"
        fi
        echo -e "${GREEN}Rebuilding and starting production environment...${NC}"
        docker-compose -f docker-compose.prod.yml up -d --build
        echo -e "${GREEN}Production API is running at http://localhost:5001${NC}"
        ;;
    clean)
        echo -e "${GREEN}Cleaning Docker resources...${NC}"
        docker-compose down --volumes --remove-orphans
        docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
        docker-compose -f docker-compose.prod.yml down --volumes --remove-orphans
        echo -e "${GREEN}Docker resources cleaned.${NC}"
        ;;
    logs)
        echo -e "${GREEN}Showing logs...${NC}"
        docker-compose logs -f
        ;;
    shell)
        echo -e "${GREEN}Opening shell in the API container...${NC}"
        docker-compose exec api /bin/bash
        ;;
    help|*)
        show_help
        ;;
esac
