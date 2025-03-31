# Production Deployment Guide - Instagram Carousel Generator API

This guide provides comprehensive instructions for deploying the Instagram Carousel Generator API to a production environment, including security hardening, scaling considerations, and monitoring best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
   - [Docker Deployment](#docker-deployment)
   - [Traditional Deployment](#traditional-deployment)
   - [Cloud Platform Deployment](#cloud-platform-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Security Hardening](#security-hardening)
5. [Scaling Considerations](#scaling-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the Instagram Carousel Generator API to production, ensure you have:

- Server with Ubuntu 20.04/22.04 LTS or similar Linux distribution
- At least 2GB RAM and 2 CPU cores
- At least 20GB of storage (more if you expect high traffic)
- Domain name configured with DNS records
- SSL certificate (Let's Encrypt or similar)
- Basic understanding of Linux server administration

## Deployment Options

### Docker Deployment

The recommended way to deploy the Instagram Carousel Generator API is using Docker. This method ensures consistency between environments and simplifies dependency management.

#### Using Docker Compose

1. Clone the repository on your production server:

```bash
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api
```

2. Create a `.env` file with your production settings:

```bash
# API Settings
API_PREFIX=/api
API_VERSION=v1
DEBUG=False
PRODUCTION=True
API_KEY=your_secure_api_key_here

# Server Settings
HOST=0.0.0.0
PORT=5001

# Public Access Settings
PUBLIC_BASE_URL=https://your-domain.com

# Path Settings
TEMP_DIR=/app/static/temp
TEMP_FILE_LIFETIME_HOURS=24

# CORS Settings
ALLOW_ORIGINS_STR=https://your-frontend-domain.com
ALLOW_CREDENTIALS=True
ALLOW_METHODS_STR=GET,POST,PUT,DELETE
ALLOW_HEADERS_STR=*

# Rate Limiting Settings
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60

# Security Settings
ENABLE_HTTPS_REDIRECT=True
```

3. Build and start the production containers:

```bash
./scripts/docker.sh prod:build
```

This will build the production Docker image and start the containers using the `docker-compose.prod.yml` configuration.

#### Manual Docker Setup

If you prefer to manage Docker without the helper script:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Traditional Deployment

For servers where Docker isn't an option, you can deploy the API directly:

1. Clone the repository:

```bash
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api
```

2. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install production dependencies:

```bash
pip install -e .
```

4. Create a `.env` file with appropriate settings (see Docker section).

5. Set up a systemd service:

```bash
sudo nano /etc/systemd/system/instagram-carousel-api.service
```

Add the following content:

```ini
[Unit]
Description=Instagram Carousel Generator API
After=network.target

[Service]
User=your_username
Group=your_username
WorkingDirectory=/path/to/instagram-carousel-api
Environment="PATH=/path/to/instagram-carousel-api/venv/bin"
ExecStart=/path/to/instagram-carousel-api/venv/bin/uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

6. Enable and start the service:

```bash
sudo systemctl enable instagram-carousel-api
sudo systemctl start instagram-carousel-api
```

7. Set up Nginx as a reverse proxy (see Nginx configuration below).

### Cloud Platform Deployment

The API can be deployed to various cloud platforms:

#### AWS Elastic Beanstalk

1. Install the AWS CLI and EB CLI.
2. Initialize the EB application:

```bash
eb init -p docker instagram-carousel-api
```

3. Create an environment:

```bash
eb create production-environment
```

4. Configure environment variables through the EB Console or:

```bash
eb setenv API_KEY=your_secure_key DEBUG=False PRODUCTION=True ...
```

#### Digital Ocean App Platform

1. Connect your repository to Digital Ocean.
2. Create a new app selecting your repository.
3. Choose the Docker deployment type.
4. Configure environment variables in the App Platform settings.

## Environment Configuration

### Nginx Configuration

For production deployments, we recommend using Nginx as a reverse proxy:

1. Install Nginx:

```bash
sudo apt update
sudo apt install nginx
```

2. Create a server configuration:

```bash
sudo nano /etc/nginx/sites-available/instagram-carousel-api
```

Add the following content:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
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

    # Serve static files directly
    location /static/ {
        alias /path/to/instagram-carousel-api/static/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Increase max body size for API requests
    client_max_body_size 10M;
}
```

3. Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/instagram-carousel-api /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### SSL Certificate with Let's Encrypt

1. Install Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

2. Obtain and configure the certificate:

```bash
sudo certbot --nginx -d your-domain.com
```

## Security Hardening

### API Security

1. **Generate a Strong API Key**:

```bash
openssl rand -hex 32
```

2. **Set Up Rate Limiting**: Configure appropriate `RATE_LIMIT_MAX_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` in your .env file.

3. **Configure Restricted CORS**: Limit `ALLOW_ORIGINS` to only the domains that need to access your API.

### File System Security

1. **Set Proper File Permissions**:

```bash
# Set appropriate permissions for app directories
sudo chown -R www-data:www-data /path/to/instagram-carousel-api/static
sudo chmod -R 750 /path/to/instagram-carousel-api/static
```

2. **Configure Automatic Cleanup**: Ensure the `TEMP_FILE_LIFETIME_HOURS` setting is appropriate for your use case.

3. **Set Up Path Validation**: The API already includes path validation, but verify it's working correctly in your production environment.

### Server Hardening

1. **Update Packages Regularly**:

```bash
sudo apt update && sudo apt upgrade -y
```

2. **Configure a Firewall**:

```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

3. **Implement Fail2Ban** to protect against brute force attacks:

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

4. **Disable Root SSH Login** and use key-based authentication.

### Secrets Management

For production environments, consider using a secrets management tool like HashiCorp Vault or cloud-specific solutions (AWS Secrets Manager, GCP Secret Manager) instead of environment variables.

## Scaling Considerations

### Vertical Scaling

For moderate traffic increases:

1. Increase the server's CPU and RAM resources
2. Optimize the API configuration for performance

### Horizontal Scaling

For high traffic scenarios:

1. **Load Balancing**: Set up multiple API instances behind a load balancer like Nginx or a cloud load balancer.

```nginx
# Example Load Balancer Configuration
upstream carousel_api {
    server 10.0.0.1:5001;
    server 10.0.0.2:5001;
    server 10.0.0.3:5001;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://carousel_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **Distributed Storage**: Consider implementing a shared file system (NFS) or object storage (S3) for carousel images.

3. **Caching**: Implement Redis or Memcached for response caching:

```python
# Example Redis configuration in config.py
class Settings(BaseSettings):
    # ... other settings

    # Redis settings for caching
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "False").lower() == "true"
```

4. **Database Integration**: For tracking carousel data, consider adding a database and implementing connection pooling.

### Containerized Scaling

For Docker deployments:

1. **Kubernetes Deployment**: For large-scale applications, consider migrating to Kubernetes for orchestration.

2. **Docker Swarm**: For simpler setups, Docker Swarm can provide basic orchestration:

```bash
# Initialize Swarm
docker swarm init

# Deploy the application
docker stack deploy -c docker-compose.prod.yml carousel-api
```

## Monitoring and Maintenance

### Logging Configuration

The API includes structured logging. Configure log aggregation:

1. **ELK Stack (Elasticsearch, Logstash, Kibana)**:
   - Collect logs with Filebeat
   - Parse with Logstash
   - Store in Elasticsearch
   - Visualize with Kibana

2. **Prometheus and Grafana** for metrics:

```bash
# Install Prometheus Node Exporter
sudo apt install prometheus-node-exporter

# Configure Prometheus to scrape metrics from your API endpoint
# Edit /etc/prometheus/prometheus.yml
```

### Monitoring Dashboard

The API includes a monitoring dashboard accessible at `/monitoring/dashboard`. Secure this endpoint with proper authentication in production.

### Health Checks

Set up external health check monitoring to your `/health` endpoint:

1. **Uptime Robot**: Configure to ping your health endpoint every 5 minutes
2. **Datadog**: Set up advanced monitoring for API performance and uptime

### Backup Strategy

1. **Code Backup**: Ensure your code is in version control
2. **Configuration Backup**: Regularly backup your `.env` and server configurations
3. **Data Backup**: If using a database, implement regular backups

## Backup and Recovery

### Backup Strategy

1. **Application Code**:
   - Ensure your source code is version-controlled with Git
   - Make regular tagged releases for production deployments

2. **Configuration**:
   - Backup `.env`, Nginx configurations, and any custom settings
   - Store backup copies of SSL certificates

3. **Automated Backups**:

```bash
# Example backup script
#!/bin/bash
BACKUP_DIR="/backup/instagram-carousel-api"
DATE=$(date +%Y-%m-%d)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup configurations
cp /path/to/instagram-carousel-api/.env $BACKUP_DIR/$DATE/
cp /etc/nginx/sites-available/instagram-carousel-api $BACKUP_DIR/$DATE/
cp -r /path/to/ssl/certificates $BACKUP_DIR/$DATE/ssl/

# Compress backup
tar -czf $BACKUP_DIR/$DATE.tar.gz $BACKUP_DIR/$DATE
rm -rf $BACKUP_DIR/$DATE

# Rotate backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -type f -mtime +30 -delete
```

### Recovery Procedures

Document step-by-step recovery procedures:

1. **Server Failure**:
   - Set up a new server with the same specifications
   - Install Docker or required dependencies
   - Restore configurations from backup
   - Redeploy the application

2. **Data Corruption**:
   - Identify corrupted data
   - Restore from the most recent backup
   - Verify system integrity after restoration

## Troubleshooting

### Common Issues

1. **API Not Starting**:
   - Check logs: `sudo journalctl -u instagram-carousel-api`
   - Verify .env configuration
   - Check for port conflicts

2. **Image Generation Errors**:
   - Verify font files are properly installed
   - Check system requirements for Pillow/PIL
   - Ensure temp directories are writable

3. **Performance Issues**:
   - Check server resources (CPU, memory, disk space)
   - Review rate limiting settings
   - Examine logging for slow requests

### Logging and Debugging

1. **Enhanced Logging**:
   - Set `LOG_LEVEL=DEBUG` temporarily for detailed logs
   - Use the `/metrics` endpoint for performance data

2. **Remote Debugging**:
   - For serious issues, set up a staging environment that mirrors production
   - Use the debug endpoints (`/debug-temp`) to check file system state

### Support Resources

- GitHub Issues: [https://github.com/kakil/instagram-carousel-api/issues](https://github.com/kakil/instagram-carousel-api/issues)
- Documentation: [https://your-domain.com/docs](https://your-domain.com/docs)
