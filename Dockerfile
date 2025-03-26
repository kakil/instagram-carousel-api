FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install fonts for image generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY requirements-dev.txt .

# Development image with hot reloading
FROM base as development

# Install dev dependencies
RUN pip install -r requirements-dev.txt

# Copy everything (for development)
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/static/temp /app/static/assets

# Expose the port
EXPOSE 5001

# Start development server
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "5001", "--reload"]

# Production image with minimal size
FROM base as production

# Install production dependencies only
RUN pip install -r requirements.txt

# Copy only necessary files for production
COPY app /app/app
COPY static /app/static
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install .

# Create necessary directories
RUN mkdir -p /app/static/temp /app/static/assets

# Expose the port
EXPOSE 5001

# Start production server
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "5001"]
