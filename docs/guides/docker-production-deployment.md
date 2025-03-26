# Docker Production Deployment Guide

This guide explains how to deploy the Instagram Carousel Generator API to production using Docker containers.

## Prerequisites

- A server with Docker and Docker Compose installed
- Domain name configured with DNS pointing to your server
- SSL certificate (recommended for production)
- Basic knowledge of Docker and Linux server administration

## Deployment Steps

### 1. Prepare the Production Server

First, ensure Docker and Docker Compose are installed on your server:

```bash
# Update package index
sudo apt update

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Add your user to docker group (optional, for management without sudo)
sudo usermod -aG docker $USER
```

### 2. Clone the Repository

Clone the repository to your server:

```bash
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api
```

### 3. Configure Environment Variables

Create a production `.env` file:

```bash
cp .env.example .env
```

Edit the `.env` file with your production settings:

```bash
# Use your favorite editor
nano .env
```

Important production settings to configure:

```
DEBUG=False
PRODUCTION=True
API_KEY=your_secure_api_key_here
PUBLIC_BASE_URL=https://api.yourdomain.com
ALLOW_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
LOG_LEVEL=INFO
ENABLE_HTTPS_REDIRECT=True
```

### 4. Deploy with Docker Compose

Use our production Docker Compose file to deploy:

```bash
# Start the production environment
docker-compose -f docker-compose.prod.yml up -d
```

This will start the application in detached mode with the production configuration.

### 5. Set Up Nginx as a Reverse Proxy

For production, it's recommended to use Nginx as a reverse proxy with SSL termination.

Create an Nginx configuration file:

```
sudo nano /etc/nginx/sites-available/api.yourdomain.com
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }

    # Let's Encrypt configuration
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/api.yourdomain.com/chain.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Serve static files directly
    location /static/ {
        alias /path/to/instagram-carousel-api/static/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Health check
    location = /health {
        proxy_pass http://localhost:5001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Add cache headers to prevent caching of health check
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/api.yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t  # Test the configuration
sudo systemctl reload nginx
```

### 6. Set Up SSL with Let's Encrypt

Install Certbot and obtain an SSL certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### 7. Monitoring and Maintenance

#### Check Container Status

```bash
docker ps
```

#### View Logs

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

#### Update the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Backup Data

Set up a cron job to back up important data:

```bash
crontab -e
```

Add a backup job:

```
# Backup carousel data daily at 2 AM
0 2 * * * tar -czf /backups/carousel-data-$(date +\%Y\%m\%d).tar.gz /path/to/instagram-carousel-api/static/assets /path/to/instagram-carousel-api/static/temp
```

### 8. Security Considerations

1. **API Key**: Ensure a strong, randomly generated API key is used
2. **Firewall**: Configure a firewall to restrict access
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```
3. **Rate Limiting**: Configure rate limiting in production settings
4. **Regular Updates**: Keep Docker, the OS, and the application updated

### 9. Performance Tuning

#### Container Resources

If you need to limit container resources, you can modify `docker-compose.prod.yml`:

```yaml
services:
  api:
    # Other configuration...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### Nginx Tuning

For high-traffic instances, consider optimizing Nginx:

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;
}

http {
    # Other configuration...

    keepalive_timeout 65;
    keepalive_requests 100;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # Gzip settings
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;
    gzip_proxied any;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rss+xml
        application/vnd.geo+json
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/bmp
        image/svg+xml
        image/x-icon
        text/cache-manifest
        text/css
        text/plain
        text/vcard
        text/vnd.rim.location.xloc
        text/vtt
        text/x-component
        text/x-cross-domain-policy;
}
```

### 10. Troubleshooting

#### Container Won't Start

```bash
# Check for errors in logs
docker-compose -f docker-compose.prod.yml logs api

# Check if ports are already in use
sudo netstat -tulpn | grep 5001
```

#### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Renew certificate if expired
sudo certbot renew
```

#### Performance Issues

```bash
# Check container resource usage
docker stats

# Check system load
top
htop  # If installed
```

## Conclusion

Your Instagram Carousel Generator API should now be running securely in production using Docker. Remember to monitor the application, perform regular backups, and keep everything updated to maintain security and performance.

For additional support, refer to the documentation or create an issue on GitHub.
