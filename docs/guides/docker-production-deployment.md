# Docker Production Deployment Guide - Instagram Carousel Generator API

This guide provides detailed instructions for deploying the Instagram Carousel Generator API to production using Docker. It covers best practices, security considerations, and performance optimizations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Production Docker Configuration](#production-docker-configuration)
3. [Deployment Architecture](#deployment-architecture)
4. [Environment Configuration](#environment-configuration)
5. [Security Best Practices](#security-best-practices)
6. [Scaling and High Availability](#scaling-and-high-availability)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [CI/CD Integration](#cicd-integration)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before proceeding with production deployment, ensure you have:

- A Linux-based server (Ubuntu 20.04/22.04 LTS recommended)
- Docker (version 20.10+) and Docker Compose (version 2.0+)
- Domain name with DNS configured
- SSH access to the server
- Basic understanding of Docker concepts

### Installation Requirements

1. Install Docker on Ubuntu:

```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to the Docker group (optional, for convenience)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

2. Test Docker installation:

```bash
docker --version
docker-compose --version
```

## Production Docker Configuration

For production deployment, we use the `docker-compose.prod.yml` file that's specifically configured for production environments.

### Understanding docker-compose.prod.yml

Here's a breakdown of our production Docker Compose configuration:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "5001:5001"
    environment:
      - DEBUG=False
      - PRODUCTION=True
      - API_PREFIX=/api
      - HOST=0.0.0.0
      - PORT=5001
      - ALLOW_ORIGINS=${ALLOW_ORIGINS:-https://kitwanaakil.com,https://admin.kitwanaakil.com}
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY}
      - PUBLIC_BASE_URL=${PUBLIC_BASE_URL:-https://api.kitwanaakil.com}
      - ENABLE_HTTPS_REDIRECT=True
    volumes:
      - carousel_temp:/app/static/temp
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - carousel-prod-network

volumes:
  carousel_temp:
    driver: local

networks:
  carousel-prod-network:
    driver: bridge
```

This configuration:
- Uses the production target in our multi-stage Dockerfile
- Sets environment variables appropriate for production
- Mounts a persistent Docker volume for temporary files
- Configures container restart policy for reliability
- Sets up healthchecks to monitor container health
- Creates a dedicated network for the application

### Deploying with Docker Compose

1. Clone the repository on your production server:

```bash
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api
```

2. Create a `.env` file with production settings:

```bash
# API Settings
API_KEY=your_secure_api_key  # Generate with: openssl rand -hex 32
API_PREFIX=/api
API_VERSION=v1
DEBUG=False
PRODUCTION=True

# Server Settings
HOST=0.0.0.0
PORT=5001

# Public Access Settings
PUBLIC_BASE_URL=https://api.yourdomain.com

# CORS Settings (comma-separated list of allowed origins)
ALLOW_ORIGINS_STR=https://yourdomain.com,https://admin.yourdomain.com
ALLOW_CREDENTIALS=True
ALLOW_METHODS_STR=GET,POST,PUT,DELETE
ALLOW_HEADERS_STR=*

# Rate Limiting Settings
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60

# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT_JSON=True

# Security Settings
ENABLE_HTTPS_REDIRECT=True
```

3. Build and start the production containers:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

4. Verify the deployment:

```bash
# Check if containers are running
docker ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check health status
curl http://localhost:5001/health
```

## Deployment Architecture

For production deployment, we recommend the following architecture:

```
                   ┌─────────────┐
                   │   Internet  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │  Cloudflare │ ◄── DNS, SSL, Security
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │    Nginx    │ ◄── Reverse Proxy
                   └──────┬──────┘
                          │
             ┌────────────▼───────────┐
             │                        │
      ┌──────▼──────┐         ┌──────▼──────┐
      │  API Docker │         │ Redis Cache │ ◄── Optional
      │  Container  │         │ (Optional)  │
      └──────┬──────┘         └─────────────┘
             │
      ┌──────▼──────┐
      │Docker Volume│ ◄── Persistent Storage
      │carousel_temp│
      └─────────────┘
```

### Nginx Configuration for Docker

Create an Nginx configuration to proxy requests to your Docker container:

```bash
sudo nano /etc/nginx/sites-available/instagram-carousel-api
```

Add the following content:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'" always;

    # Main API proxy
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }

    # Increase max body size for API requests
    client_max_body_size 10M;
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/instagram-carousel-api /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Environment Configuration

### Using Environment Variables in Docker

When deploying with Docker, there are several ways to manage environment variables:

1. **Using the .env file** (our recommended approach):
   - Create the `.env` file in the same directory as your docker-compose.yml
   - Docker Compose automatically loads this file

2. **Passing variables directly**:
   ```bash
   API_KEY=your_key PUBLIC_BASE_URL=https://api.example.com docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Using environment files with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
   ```

### Multi-Environment Configuration

For organizations with multiple environments (development, staging, production):

1. Create separate .env files:
   - `.env.development`
   - `.env.staging`
   - `.env.production`

2. Use a script to deploy to the correct environment:

```bash
#!/bin/bash
# deploy.sh
ENV=$1

if [ -z "$ENV" ]
then
    echo "Usage: ./deploy.sh [development|staging|production]"
    exit 1
fi

if [ ! -f ".env.$ENV" ]
then
    echo "Environment file .env.$ENV not found!"
    exit 1
fi

echo "Deploying to $ENV environment..."
cp ".env.$ENV" .env
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Deploy to an environment:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh production
   ```

## Security Best Practices

### Secure Docker Configuration

1. **Run containers as non-root users**:
   - Our Dockerfile already follows this practice
   - Verify with: `docker exec -it container_name id`

2. **Limit container resources**:
   - Add these constraints to the `docker-compose.prod.yml` file:
   ```yaml
   services:
     api:
       # ... other configuration
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 1G
           reservations:
             cpus: '0.5'
             memory: 512M
   ```

3. **Use Docker secrets for sensitive data** (for Docker Swarm deployments):
   ```bash
   # Create a secret
   echo "your_secure_api_key" | docker secret create api_key -

   # Use the secret in docker-compose.yml
   services:
     api:
       # ... other configuration
       secrets:
         - api_key

   secrets:
     api_key:
       external: true
   ```

4. **Regularly update the base images**:
   ```bash
   # Pull latest base image
   docker pull python:3.10-slim

   # Rebuild your images
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

5. **Scan for vulnerabilities**:
   ```bash
   # Using Docker Scout (built into Docker Desktop)
   docker scout cves instagram-carousel-api:latest

   # Or Trivy
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image instagram-carousel-api:latest
   ```

### API Security

1. **Properly configure CORS**:
   - Restrict `ALLOW_ORIGINS` to only your frontend domains
   - Don't use wildcard (*) in production

2. **Implement proper rate limiting**:
   - Adjust `RATE_LIMIT_MAX_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` based on expected usage
   - Monitor for abuse patterns

3. **Use strong API keys**:
   - Generate with: `openssl rand -hex 32`
   - Rotate keys periodically
   - Never commit keys to version control

4. **Configure filesystem security**:
   - The Docker volume `carousel_temp` should be used for all temporary files
   - Data in this volume persists across container restarts but is isolated from the host

## Scaling and High Availability

The Instagram Carousel Generator API can be scaled horizontally to handle increased traffic and provide high availability.

### Docker Compose Scaling

For basic scaling with Docker Compose:

```bash
# Start multiple instances of the API service
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

However, for this to work properly with multiple instances:

1. **Update the ports configuration** in `docker-compose.prod.yml`:
   ```yaml
   services:
     api:
       # ... other configuration
       ports:
         - "5001"  # Remove the host port binding
   ```

2. **Add a load balancer** in front of the API instances:
   ```yaml
   services:
     api:
       # ... configuration without fixed port binding

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
       depends_on:
         - api
   ```

3. **Create an Nginx configuration** for load balancing:
   ```nginx
   # nginx.conf
   events {
       worker_connections 1024;
   }

   http {
       upstream carousel_api {
           server api:5001;
       }

       server {
           listen 80;

           location / {
               proxy_pass http://carousel_api;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
           }
       }
   }
   ```

### Docker Swarm Deployment

For production-grade scaling and high availability, Docker Swarm provides a better solution:

1. **Initialize a Docker Swarm**:
   ```bash
   docker swarm init
   ```

2. **Create a Docker Stack file** (`docker-stack.yml`):
   ```yaml
   version: '3.8'

   services:
     api:
       image: instagram-carousel-api:latest
       environment:
         - DEBUG=False
         - PRODUCTION=True
         - API_PREFIX=/api
         - HOST=0.0.0.0
         - PORT=5001
         - ALLOW_ORIGINS=${ALLOW_ORIGINS}
         - API_KEY=${API_KEY}
         - PUBLIC_BASE_URL=${PUBLIC_BASE_URL}
       volumes:
         - carousel_temp:/app/static/temp
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
         interval: 30s
         timeout: 10s
         retries: 3
       deploy:
         replicas: 3
         update_config:
           parallelism: 1
           delay: 10s
           order: start-first
         restart_policy:
           condition: on-failure
           max_attempts: 3
         resources:
           limits:
             cpus: '0.5'
             memory: 512M

     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
       depends_on:
         - api
       deploy:
         replicas: 2
         placement:
           constraints: [node.role == manager]

   volumes:
     carousel_temp:
       driver: local
   ```

3. **Deploy the stack**:
   ```bash
   docker stack deploy -c docker-stack.yml carousel
   ```

4. **Monitor the deployment**:
   ```bash
   docker stack services carousel
   docker service logs carousel_api
   ```

### Shared Storage Considerations

When running multiple API instances, consider how temporary files are shared:

1. **Docker named volumes** (used in the examples above):
   - Work well for single-node deployments
   - For multi-node Swarm clusters, use a volume driver that supports sharing

2. **NFS volumes** for multi-server deployments:
   ```yaml
   volumes:
     carousel_temp:
       driver: local
       driver_opts:
         type: "nfs"
         o: "addr=nfs-server.example.com,nolock,soft,rw"
         device: ":/path/to/shared/directory"
   ```

3. **Object storage** (Amazon S3, MinIO, etc.) for cloud deployments:
   - Requires code changes to store files in object storage instead of local filesystem
   - More scalable for production deployments

## Monitoring and Logging

### Container-Level Monitoring

1. **Basic Docker monitoring**:
   ```bash
   # View container metrics
   docker stats

   # Monitor container logs
   docker logs -f container_id
   ```

2. **Using Prometheus with cAdvisor**:
   - Add cAdvisor to `docker-compose.prod.yml`:
   ```yaml
   services:
     # ... other services

     cadvisor:
       image: gcr.io/cadvisor/cadvisor:latest
       container_name: cadvisor
       ports:
         - "8080:8080"
       volumes:
         - /:/rootfs:ro
         - /var/run:/var/run:ro
         - /sys:/sys:ro
         - /var/lib/docker/:/var/lib/docker:ro
       restart: always

     prometheus:
       image: prom/prometheus:latest
       container_name: prometheus
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
       depends_on:
         - cadvisor
       restart: always
   ```

   - Create a Prometheus configuration file:
   ```yaml
   # prometheus.yml
   global:
     scrape_interval: 15s

   scrape_configs:
     - job_name: 'prometheus'
       static_configs:
         - targets: ['localhost:9090']

     - job_name: 'cadvisor'
       static_configs:
         - targets: ['cadvisor:8080']

     - job_name: 'instagram-carousel-api'
       static_configs:
         - targets: ['api:5001']
       metrics_path: '/metrics'
   ```

3. **Grafana for visualization**:
   - Add to Docker Compose:
   ```yaml
   services:
     # ... other services

     grafana:
       image: grafana/grafana:latest
       container_name: grafana
       ports:
         - "3000:3000"
       depends_on:
         - prometheus
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=secure_password
       restart: always
   ```

### API-Level Monitoring

1. **Health checks**:
   - The API includes a `/health` endpoint for basic health checks
   - The Docker configuration includes a health check command

2. **Using the monitoring dashboard**:
   - Access the built-in monitoring dashboard at `/monitoring/dashboard`
   - Secure this endpoint with proper authentication
   - The dashboard provides insights into API performance and usage

3. **Custom metrics collection**:
   - Use the `/metrics` endpoint for detailed API metrics
   - Integrate with Prometheus for historical data and alerting
   - Create custom Grafana dashboards for visualizing metrics

### Centralized Logging

1. **Using Docker's built-in logging**:
   ```bash
   # View logs for all services
   docker-compose -f docker-compose.prod.yml logs -f

   # View logs for a specific service
   docker-compose -f docker-compose.prod.yml logs -f api
   ```

2. **ELK Stack (Elasticsearch, Logstash, Kibana)**:
   - Add to Docker Compose:
   ```yaml
   services:
     # ... other services

     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:7.16.3
       environment:
         - discovery.type=single-node
         - ES_JAVA_OPTS=-Xms512m -Xmx512m
       volumes:
         - elasticsearch_data:/usr/share/elasticsearch/data

     logstash:
       image: docker.elastic.co/logstash/logstash:7.16.3
       volumes:
         - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
       depends_on:
         - elasticsearch

     kibana:
       image: docker.elastic.co/kibana/kibana:7.16.3
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch

   volumes:
     elasticsearch_data:
   ```

   - Create Logstash configuration:
   ```
   # logstash.conf
   input {
     tcp {
       port => 5000
       codec => json
     }
   }

   output {
     elasticsearch {
       hosts => ["elasticsearch:9200"]
       index => "instagram-carousel-api-%{+YYYY.MM.dd}"
     }
   }
   ```

   - Update the API service to use the logstash driver:
   ```yaml
   services:
     api:
       # ... other configuration
       logging:
         driver: "gelf"
         options:
           gelf-address: "udp://localhost:12201"
           tag: "carousel-api"
   ```

### Alerting

1. **Set up alerting in Grafana**:
   - Configure alerts based on API performance metrics
   - Send notifications via email, Slack, or other channels

2. **Prometheus alerting**:
   - Use AlertManager with Prometheus for advanced alerting
   - Create alerting rules based on metrics thresholds

## Backup and Recovery

### Docker Volume Backups

1. **Backing up the carousel_temp volume**:

```bash
# Create a backup container to access the volume
docker run --rm -v carousel_temp:/source -v $(pwd)/backups:/backup alpine \
    tar -czf /backup/carousel_temp_$(date +%Y%m%d).tar.gz -C /source .
```

2. **Restoring from backup**:

```bash
# Create a restore container
docker run --rm -v carousel_temp:/target -v $(pwd)/backups:/backup alpine \
    sh -c "rm -rf /target/* && tar -xzf /backup/carousel_temp_20230101.tar.gz -C /target"
```

3. **Automated backup script**:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Back up Docker volume
docker run --rm -v carousel_temp:/source -v $BACKUP_DIR:/backup alpine \
    tar -czf /backup/carousel_temp_$DATE.tar.gz -C /source .

# Clean up old backups
find $BACKUP_DIR -name "carousel_temp_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/carousel_temp_$DATE.tar.gz"
```

### Docker Compose Configuration Backup

1. **Version control** (recommended method):
   - Store Docker Compose files and configurations in Git
   - Tag releases for easy rollback

2. **Manual configuration backup**:

```bash
# Create a configurations backup
mkdir -p /path/to/backups/configs_$(date +%Y%m%d)
cp docker-compose.prod.yml /path/to/backups/configs_$(date +%Y%m%d)/
cp .env /path/to/backups/configs_$(date +%Y%m%d)/
cp nginx.conf /path/to/backups/configs_$(date +%Y%m%d)/
```

### Recovery Procedures

Document recovery procedures for different failure scenarios:

1. **Container failure**:
   - Automatic restart is configured in Docker Compose
   - For manual restart: `docker-compose -f docker-compose.prod.yml up -d --no-recreate`

2. **Host server failure**:
   - Set up the new server with Docker
   - Restore configuration files from backup
   - Restore volume data from backup
   - Redeploy containers

3. **Data corruption**:
   - Stop the services: `docker-compose -f docker-compose.prod.yml down`
   - Restore the volume from backup
   - Restart services: `docker-compose -f docker-compose.prod.yml up -d`

## CI/CD Integration

Implementing CI/CD will automate testing, building, and deployment of your Docker containers.

### GitHub Actions Setup

1. **Create a GitHub Actions workflow file** (`.github/workflows/docker-deploy.yml`):

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1

      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v3
        with:
          images: yourusername/instagram-carousel-api
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha

      - name: Build and push Docker image
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          target: production
          cache-from: type=registry,ref=yourusername/instagram-carousel-api:latest
          cache-to: type=inline

  deploy:
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/instagram-carousel-api
            git pull
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
```

2. **Set up required GitHub Secrets**:
   - DOCKERHUB_USERNAME: Your Docker Hub username
   - DOCKERHUB_TOKEN: Your Docker Hub access token
   - SSH_HOST: Your server's IP address
   - SSH_USERNAME: SSH username for the server
   - SSH_PRIVATE_KEY: SSH private key for server access

### GitLab CI/CD Setup

1. **Create a GitLab CI/CD configuration file** (`.gitlab-ci.yml`):

```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

test:
  stage: test
  image: python:3.10
  script:
    - pip install -e ".[dev]"
    - pytest

build:
  stage: build
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build --target production -t $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
    - |
      if [[ "$CI_COMMIT_REF_NAME" == "main" ]]; then
        docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
      fi

deploy:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - ssh -o StrictHostKeyChecking=no $SSH_USER@$SSH_HOST "cd /path/to/instagram-carousel-api && docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
:
    - tags
```
