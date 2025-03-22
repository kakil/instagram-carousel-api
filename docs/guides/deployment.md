# Instagram Carousel Generator - Production Deployment Guide

This guide provides step-by-step instructions for deploying the Instagram Carousel Generator API in a production environment. We'll cover various deployment options from traditional server setup to containerized deployments.

## Pre-Deployment Checklist

Before deploying to production, ensure you've completed the following:

- [x] Test the application thoroughly in your development environment
- [x] Create a production-specific `.env` file with secure settings
- [x] Set a strong API key for authentication
- [x] Configure appropriate CORS settings
- [x] Set up proper logging
- [x] Enable HTTPS/SSL

## Option 1: Traditional Server Deployment

### Step 1: Set Up the Server

1. Provision a VPS or dedicated server (recommended specs: 1+ CPU cores, 2+ GB RAM)
2. Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

3. Install required dependencies:

```bash
sudo apt install -y python3 python3-pip python3-venv nginx
```

### Step 2: Clone and Set Up the Application

1. Clone the repository:

```bash
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Create production environment file:

```bash
cp .env.example .env
nano .env
```

5. Update the `.env` file with production settings:

```
DEBUG=False
PRODUCTION=True
PUBLIC_BASE_URL=https://api.yourdomain.com
API_KEY=your-secure-api-key
ALLOW_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
```

### Step 3: Configure Nginx

1. Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/instagram-carousel-api
```

2. Add the following configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Proxy to uvicorn server
    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Serve temp files directly for better performance
    location /api/v1/temp/ {
        alias /path/to/instagram-carousel-api/static/temp/;
        expires 24h;
        add_header Cache-Control "public";
    }

    # Static files with longer cache
    location /static/ {
        alias /path/to/instagram-carousel-api/static/;
        expires 7d;
        add_header Cache-Control "public";
    }