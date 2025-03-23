# Setting Up Systemd Service for Production

This guide explains how to set up a systemd service for the Instagram Carousel Generator on your production server.

## Create the Service File

Create a new file at `/etc/systemd/system/instagram-carousel-api.service` with the following content:

```ini
[Unit]
Description=Instagram Carousel Generator API
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/app/current
ExecStart=/path/to/app/current/venv/bin/uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5001
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=instagram-carousel-api
Environment="PYTHONPATH=/path/to/app/current"
Environment="PRODUCTION=true"
Environment="DEBUG=false"

# Read environment variables from a file
EnvironmentFile=/path/to/app/current/.env

[Install]
WantedBy=multi-user.target
```

Replace `your_username` and `/path/to/app` with your actual username and application path.

## Enable and Start the Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable instagram-carousel-api

# Start the service
sudo systemctl start instagram-carousel-api
```

## Check Service Status

```bash
# Check if the service is running
sudo systemctl status instagram-carousel-api

# View service logs
sudo journalctl -u instagram-carousel-api -f
```

## Managing the Service

```bash
# Restart the service (e.g., after deploying updates)
sudo systemctl restart instagram-carousel-api

# Stop the service
sudo systemctl stop instagram-carousel-api

# Start the service
sudo systemctl start instagram-carousel-api
```

## Troubleshooting

### Service Fails to Start

Check the logs for error messages:

```bash
sudo journalctl -u instagram-carousel-api -e
```

Common issues include:
- Wrong paths in the service file
- Missing environment variables
- Permission problems
- Port already in use

### Environment Variables

Make sure your `.env` file has the correct format:

```
VARIABLE_NAME=value
ANOTHER_VARIABLE=another_value
```

There should be no spaces around the `=` sign and no quotes unless they're part of the value.

### Permissions

Ensure the service user has access to all necessary files and directories:

```bash
# Give your user ownership of the application directory
sudo chown -R your_username:your_username /path/to/app

# Make sure files are readable
chmod -R 755 /path/to/app
```

## Automatic Deployment

The GitHub Actions workflow in this project is set up to automatically deploy updates and restart this service. The workflow:

1. Uploads the new code to the server
2. Installs dependencies in a virtual environment
3. Creates a symlink to the new deployment
4. Restarts the service using `sudo systemctl restart instagram-carousel-api`

The sudo permission needs to be configured to allow your deployment user to restart the service without a password:

```bash
# Add this line to sudoers (use visudo to edit)
your_username ALL=(ALL) NOPASSWD: /bin/systemctl restart instagram-carousel-api
```