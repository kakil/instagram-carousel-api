# Cloudflare Integration Guide - Instagram Carousel Generator API

This guide provides detailed instructions for integrating the Instagram Carousel Generator API with Cloudflare for enhanced security, performance, and reliability in your production environment.

## Table of Contents

1. [Introduction](#introduction)
2. [DNS Configuration](#dns-configuration)
3. [SSL/TLS Setup](#ssltls-setup)
4. [Security Optimizations](#security-optimizations)
5. [Performance Optimizations](#performance-optimizations)
6. [Rate Limiting and Bot Protection](#rate-limiting-and-bot-protection)
7. [Monitoring with Cloudflare Analytics](#monitoring-with-cloudflare-analytics)
8. [Troubleshooting](#troubleshooting)

## Introduction

Cloudflare provides several benefits for your Instagram Carousel Generator API deployment:

- **DDoS protection** to keep your API available during attacks
- **Global CDN** to cache static assets and reduce latency
- **Web Application Firewall (WAF)** to protect against common vulnerabilities
- **SSL certificates** for secure HTTPS connections
- **Analytics and monitoring** for traffic insights

## DNS Configuration

### Setting Up DNS Records

1. **Login to Cloudflare** and select your domain.

2. **Navigate to DNS** and add the following records:

   - **A Record** pointing to your VPS IP address:
     - Type: A
     - Name: api (for api.yourdomain.com) or @ (for yourdomain.com)
     - Content: [Your Contabo VPS IP address]
     - Proxy status: Proxied (orange cloud)
     - TTL: Auto

   - **CNAME Record** for www subdomain (if needed):
     - Type: CNAME
     - Name: www
     - Content: yourdomain.com
     - Proxy status: Proxied
     - TTL: Auto

3. **Verify DNS propagation** using a tool like [dnschecker.org](https://dnschecker.org/).

### Configuring Cloudflare Proxy

Ensure you're using Cloudflare as a proxy (not just DNS):

1. Go to the **DNS** tab.
2. Make sure your API domain has the **Proxy status** set to "Proxied" (orange cloud icon).
3. If not, click the gray cloud icon to change it to the orange cloud.

## SSL/TLS Setup

### Configuring SSL/TLS

1. Go to **SSL/TLS** > **Overview**.

2. Set SSL/TLS encryption mode to **Full (strict)** for the best security.
   - This setting requires a valid SSL certificate on your origin server (Contabo VPS).

3. Enable **Always Use HTTPS** under the **Edge Certificates** tab.

4. Enable **Automatic HTTPS Rewrites** to prevent mixed content warnings.

### Origin Server SSL Certificates

For Full (strict) mode, you need a valid SSL certificate on your origin server:

1. **Option 1: Origin Certificate from Cloudflare**:
   - Go to **SSL/TLS** > **Origin Server**
   - Click **Create Certificate**
   - Choose an appropriate validity period
   - Install the private key and certificate on your Nginx server

2. **Option 2: Let's Encrypt Certificate**:
   - Install Certbot on your server:
     ```bash
     sudo apt update
     sudo apt install certbot python3-certbot-nginx
     ```
   - Temporarily set DNS record to "DNS only" (gray cloud) in Cloudflare
   - Run Certbot:
     ```bash
     sudo certbot --nginx -d api.yourdomain.com
     ```
   - Return DNS record to "Proxied" (orange cloud) in Cloudflare

## Security Optimizations

### Web Application Firewall (WAF)

1. Go to **Security** > **WAF**.

2. Enable **Managed Rules** for protection against common vulnerabilities:
   - Enable OWASP Core Rule Set
   - Enable Cloudflare Managed Rules

3. Create **Custom Rules** for the Instagram Carousel Generator API:
   - Create a rule to restrict access to admin endpoints:
     ```
     (http.request.uri.path contains "/monitoring/dashboard") and (not ip.src in {your_office_ip_1 your_office_ip_2})
     ```
     Action: Block

   - Create a rule for high-risk countries (if applicable):
     ```
     (ip.geoip.country in {"XX" "YY" "ZZ"}) and (http.request.uri.path contains "/api/")
     ```
     Action: Challenge or Block

### Firewall Rules for API Keys

Create a firewall rule to enforce the presence of API keys:

1. Go to **Security** > **WAF** > **Custom Rules**.

2. Create a new rule:
   - Name: "Require API Key"
   - Expression:
     ```
     (http.request.uri.path contains "/api/v1/") and (not http.request.headers["X-API-Key"] exists)
     ```
   - Action: Block
   - Description: "Block requests without required API key"

### Additional Security Settings

1. Go to **SSL/TLS** > **Edge Certificates**.

2. Enable **HSTS** (HTTP Strict Transport Security) with these settings:
   - Max Age: 6 months
   - Include subdomains: On
   - Preload: On

3. Configure **Minimum TLS Version** to 1.2 or 1.3 for stronger encryption.

4. Set appropriate security headers in your Nginx configuration:
   ```nginx
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'" always;
   ```

## Performance Optimizations

### Caching Configuration

1. Go to **Caching** > **Configuration**.

2. Set appropriate **Browser Cache TTL** (e.g., 4 hours).

3. Enable **Always Online** for resilience during origin server downtime.

4. Configure **Caching Level** to "Standard" unless you have specific requirements.

### Page Rules for Caching Static Assets

Create page rules to optimize caching for static assets:

1. Go to **Rules** > **Page Rules**.

2. Create a rule for static assets:
   - URL: `*yourdomain.com/static/*`
   - Settings:
     - Cache Level: Cache Everything
     - Browser Cache TTL: 1 day
     - Edge Cache TTL: 1 day

3. Create a rule for API responses that can be cached:
   - URL: `*yourdomain.com/api/v1/temp/*`
   - Settings:
     - Cache Level: Cache Everything
     - Browser Cache TTL: 1 hour
     - Edge Cache TTL: 1 hour

### Cloudflare Argo (Optional)

For improved routing and performance:

1. Go to **Traffic** > **Argo**.
2. Enable **Argo Smart Routing** for faster connections to your origin.
3. Consider enabling **Argo Tiered Cache** for larger deployments.

## Rate Limiting and Bot Protection

### Rate Limiting Rules

1. Go to **Security** > **Rate Limiting**.

2. Create a rate limiting rule for API endpoints:
   - Name: "API Rate Limit"
   - URL pattern: `/api/v1/*`
   - Threshold: 60 requests per minute
   - Action: "Simulate" (for testing) then "Block"
   - Response: Custom response with status code 429

### Bot Protection

1. Go to **Security** > **Bots**.

2. Set Bot Fight Mode to "On" for basic protection.

3. For advanced protection, enable **Super Bot Fight Mode** (requires Cloudflare Pro or higher).

4. Configure bot management to detect and mitigate API abuse:
   - Go to **Security** > **Bot Management**
   - Enable "Definitely Automated" and "Likely Automated" detection
   - Configure appropriate actions for different bot scores

### CAPTCHA Protection for High-Risk Requests

For endpoints that might be subject to abuse:

1. Go to **Security** > **WAF** > **Custom Rules**.

2. Create a rule that triggers CAPTCHA challenges for suspicious patterns:
   ```
   (http.request.uri.path contains "/api/v1/generate-carousel") and (cf.threat_score > 25)
   ```
   Action: CAPTCHA

## Monitoring with Cloudflare Analytics

### Dashboard Setup

1. Go to **Analytics & Logs** > **Traffic**.

2. Review traffic patterns, focusing on:
   - Request counts
   - Status codes
   - Cache performance
   - Security events

### Email Alerts

Configure alerts for significant changes:

1. Go to **Analytics & Logs** > **Notifications**.

2. Set up alerts for:
   - Traffic spikes
   - Origin server errors
   - Firewall events
   - Attack mitigation

### Traffic Monitoring with GraphQL API (Advanced)

For programmatic access to analytics:

1. Go to **Analytics & Logs** > **GraphQL**.

2. Use the GraphQL API to query for specific metrics:
   ```graphql
   {
     viewer {
       zones(filter: {zoneTag: "your_zone_id"}) {
         httpRequests1dGroups(limit: 7, filter: {date_gt: "2023-01-01"}) {
           dimensions {
             date
           }
           sum {
             requests
             bytes
             cachedRequests
             cachedBytes
             threats
           }
         }
       }
     }
   }
   ```

3. Integrate this with your monitoring solution for custom dashboards.

## Troubleshooting

### Common Issues and Solutions

1. **Origin Connection Errors**:
   - Verify your server is running and accessible
   - Check Nginx configuration for correct proxy settings
   - Ensure your server's firewall allows Cloudflare IPs

2. **SSL Handshake Errors**:
   - Verify SSL certificate on your origin server
   - Check SSL mode in Cloudflare is appropriate
   - Ensure certificate is valid and not expired

3. **Caching Issues**:
   - Review Cache-Control headers in your API responses
   - Check page rules for conflicting settings
   - Use the Cloudflare Cache Test tool to verify behavior

### Contacting Cloudflare Support

For issues that you can't resolve:

1. Go to **Help** > **Support**.
2. Create a support ticket with detailed information:
   - Domain name
   - Error messages
   - Steps to reproduce
   - Relevant Rayids (found in HTTP response headers)

### Checking Cloudflare Status

If you suspect a Cloudflare outage:

1. Visit [Cloudflare Status](https://www.cloudflarestatus.com/)
2. Check for any reported incidents affecting your region or services

## Additional Recommendations

### Workers for Edge Computation (Advanced)

For edge-based routing, auth, or transformation:

1. Go to **Workers & Pages**.
2. Create a Worker to:
   - Rewrite request/response headers
   - Implement geo-based routing
   - Add additional authentication layers

### Real User Monitoring

To track actual user performance:

1. Go to **Speed** > **Optimization**.
2. Enable Cloudflare Web Analytics for real user metrics.

### Optimizing for Mobile Users

1. Go to **Speed** > **Optimization**.
2. Enable Mobile Redirect for mobile-specific experiences.
3. Enable Auto Minify for HTML, CSS, and JavaScript to reduce payload size.
