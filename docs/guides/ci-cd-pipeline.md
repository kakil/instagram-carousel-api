# CI/CD Pipeline Guide

This document explains how to set up and use the CI/CD pipeline for the Instagram Carousel Generator project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions. It automates the following processes:

1. **Testing**: Runs linting, formatting checks, and unit/integration tests
2. **Code Quality**: Performs security scanning and code quality analysis
3. **Building**: Builds Docker images and Python packages
4. **Deployment**: Deploys the application to production servers
5. **Releases**: Creates GitHub releases and publishes packages to PyPI

## Workflow Files

The pipeline is defined by several workflow files in the `.github/workflows` directory:

- `test.yml`: Runs on every push and pull request to test the code
- `code-quality.yml`: Runs code quality and security checks
- `docker.yml`: Builds and pushes Docker images
- `deploy.yml`: Deploys the application to production
- `release.yml`: Creates releases when a new tag is pushed

## Setting Up GitHub Secrets

To use these workflows, you need to set up the following secrets in your GitHub repository:

| Secret Name | Description |
|-------------|-------------|
| `SSH_PRIVATE_KEY` | SSH private key for deploying to the server |
| `SERVER_IP` | IP address of the production server |
| `SERVER_USER` | SSH username for the production server |
| `DEPLOY_PATH` | Path to deploy the application on the server |
| `ENV_FILE_CONTENT` | Content of the .env file to use in production |
| `SLACK_WEBHOOK` | Webhook URL for Slack notifications |
| `DOCKERHUB_USERNAME` | DockerHub username for publishing images |
| `DOCKERHUB_TOKEN` | DockerHub access token |
| `PYPI_USERNAME` | PyPI username for publishing packages |
| `PYPI_PASSWORD` | PyPI password or token |

### Setting Up Secrets in GitHub

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add each of the secrets listed above

## Branch Strategy

The CI/CD pipeline is designed to work with the following branch strategy:

- `main`: Production branch. Pushes to this branch trigger tests and deployment.
- `develop`: Development branch. Pushes trigger tests but not deployment.
- Feature branches: Created for new features, merged to `develop` via pull requests.

## Workflow Triggers

- **Test workflow**: Runs on push to any branch and on pull requests to `main` and `develop`
- **Code Quality workflow**: Runs on push to `main` and `develop`, on pull requests, and weekly
- **Docker workflow**: Runs on push to `main` and `develop`, and when tags are pushed
- **Deploy workflow**: Runs on push to `main` and can be triggered manually
- **Release workflow**: Runs when a tag with the format `v*` is pushed

## Continuous Integration

The CI part of the pipeline automatically runs tests and checks code quality. This helps catch issues early in the development process.

### Automated Tests

Tests are run using pytest. The pipeline runs:

```bash
pytest tests/
```

### Code Quality Checks

Code quality is checked using:

- **flake8**: For linting
- **black**: For code formatting
- **mypy**: For type checking
- **bandit**: For security scanning
- **safety**: For dependency vulnerability scanning

## Continuous Deployment

The CD part of the pipeline automatically deploys the application to production when changes are pushed to the `main` branch.

### Deployment Process

1. The code is tested to ensure it passes all checks
2. The code is packaged and deployed to the production server via SSH
3. Dependencies are installed in a virtual environment
4. The application service is restarted
5. A health check verifies the deployment
6. Slack notifications are sent on success or failure

### Manual Deployment

You can trigger a manual deployment by:

1. Going to the "Actions" tab in your GitHub repository
2. Selecting the "Deploy to Production" workflow
3. Clicking "Run workflow"
4. Entering a reason for the manual deployment
5. Clicking "Run workflow" again

## Creating Releases

To create a new release:

1. Update the version in `app/__init__.py`
2. Update the `CHANGELOG.md` file with details of the changes
3. Commit and push these changes
4. Create and push a new tag:
   ```bash
   git tag -a v1.0.1 -m "Version 1.0.1"
   git push origin v1.0.1
   ```

This will trigger the release workflow, which will:
1. Create a GitHub release with notes extracted from the CHANGELOG
2. Build and publish a Python package to PyPI
3. Build and publish a Docker image with the version tag

## Monitoring Workflows

You can monitor workflow runs in the "Actions" tab of your GitHub repository. Each run shows:

- The trigger event (push, pull request, etc.)
- The status (in progress, successful, failed)
- Detailed logs for debugging

## Troubleshooting

If a workflow fails, check the following:

1. **Tests failures**: Look at the test logs to see which tests failed
2. **Deployment failures**: Check if the server is accessible and has the necessary permissions
3. **Docker build failures**: Check if the Dockerfile is correct and all dependencies are available
4. **Release failures**: Ensure the version follows semantic versioning and the CHANGELOG is properly formatted

For server-side issues, check the server logs:

```bash
sudo journalctl -u instagram-carousel-api -f
```