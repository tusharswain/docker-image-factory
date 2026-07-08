# Docker Image Factory Framework

A comprehensive framework for building, scanning, signing, and pushing Docker images with support for multiple languages and automated security workflows.

## Features

- **Multi-Language Support**: Python, Java, Node.js, Groovy, Robot Framework, Go, .NET
- **Automated Dockerfile Generation**: Optimized multi-stage Dockerfiles for each language
- **Security Scanning**: Integration with Trivy and Snyk for vulnerability detection
- **Image Signing**: Support for Cosign and Docker Content Trust
- **Registry Push**: Automated push to Amazon ECR or DockerHub
- **HTML Reports**: Beautiful build reports with vulnerability summaries
- **Notifications**: Slack and Email notifications on build completion/failure
- **Metadata Storage**: Store build metadata in DynamoDB, S3, or local filesystem
- **Custom Base Images**: Support for custom base images as input parameter
- **CLI Interface**: Easy-to-use command-line interface

## Prerequisites

- Python 3.8 or higher
- Docker
- Trivy (for security scanning)
- Cosign (for image signing, optional)
- AWS CLI (for ECR/DynamoDB/S3 support, optional)
- Snyk CLI (for Snyk scanning, optional)

## Installation

1. Clone or download the framework:
```bash
cd Docker-image-factory-framework
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install external tools:

**Trivy** (required for security scanning):
```bash
# macOS
brew install trivy

# Linux
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

**Cosign** (optional, for image signing):
```bash
# macOS
brew install cosign

# Linux
go install github.com/sigstore/cosign/cmd/cosign@latest
```

**AWS CLI** (optional, for ECR/DynamoDB/S3):
```bash
pip install awscli
aws configure
```

## Configuration

### Using config.yaml

Edit `config.yaml` to configure the framework:

```yaml
# General settings
log_dir: logs
default_registry: dockerhub

# Security settings
security:
  severity_threshold: HIGH

# Trivy scanner settings
trivy:
  enabled: true

# Image signing settings
signing:
  default_method: cosign

# DockerHub settings
dockerhub:
  username: your_username
  password: your_password

# Slack notification settings
slack:
  enabled: true
  webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Using Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your actual values
```

Or set environment variables directly:

```bash
export DOCKER_FACTORY_DOCKERHUB_USERNAME=your_username
export DOCKER_FACTORY_DOCKERHUB_PASSWORD=your_password
export DOCKER_FACTORY_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Usage

### Basic Usage

Build a Docker image with the full pipeline:

```bash
python docker_image_factory.py \
  --language python \
  --app-path /path/to/your/app \
  --image-name my-app \
  --image-tag v1.0.0
```

### Advanced Usage

#### Custom Base Image

```bash
python docker_image_factory.py \
  --language python \
  --app-path /path/to/your/app \
  --image-name my-app \
  --base-image python:3.12-slim
```

#### Push to ECR

```bash
python docker_image_factory.py \
  --language java \
  --app-path /path/to/your/app \
  --image-name my-java-app \
  --registry ecr
```

#### Skip Security Scanning

```bash
python docker_image_factory.py \
  --language node \
  --app-path /path/to/your/app \
  --image-name my-node-app \
  --skip-scan
```

#### Skip Image Signing

```bash
python docker_image_factory.py \
  --language go \
  --app-path /path/to/your/app \
  --image-name my-go-app \
  --skip-sign
```

#### Skip Registry Push

```bash
python docker_image_factory.py \
  --language dotnet \
  --app-path /path/to/your/app \
  --image-name my-dotnet-app \
  --skip-push
```

#### Custom Dockerfile Arguments

```bash
python docker_image_factory.py \
  --language python \
  --app-path /path/to/your/app \
  --image-name my-app \
  --custom-args '{"python_version": "3.12-slim", "port": 8080}'
```

#### Use Docker Content Trust instead of Cosign

```bash
python docker_image_factory.py \
  --language python \
  --app-path /path/to/your/app \
  --image-name my-app \
  --sign-method docker-trust
```

### Supported Languages

- **python**: Python applications
- **java**: Java applications (Maven/Gradle)
- **node**: Node.js applications
- **groovy**: Groovy applications
- **robot**: Robot Framework test suites
- **go**: Go applications
- **dotnet**: .NET applications

### CLI Options

```
--language, -l       Programming language/framework (required)
--app-path, -a       Path to application source code (required)
--image-name, -i     Name for the Docker image (required)
--image-tag, -t      Tag for the Docker image (default: latest)
--base-image, -b     Custom base image
--registry, -r       Target registry (ecr or dockerhub)
--sign-method, -s    Image signing method (cosign or docker-trust)
--config, -c         Path to configuration file
--skip-scan          Skip security scanning
--skip-sign          Skip image signing
--skip-push          Skip registry push
--custom-args        JSON string of custom arguments for Dockerfile generation
```

## Dockerfile Templates

The framework generates optimized multi-stage Dockerfiles for each language:

### Python

- Multi-stage build with builder and runtime stages
- Non-root user for security
- Health checks
- Customizable Python version and port

### Java

- Support for Maven and Gradle
- Multi-stage build with JAR optimization
- Eclipse Temurin runtime
- Health checks

### Node.js

- Multi-stage build with dependency caching
- Production-optimized builds
- Non-root user
- Health checks

### Go

- Multi-stage build with static binary
- Minimal Alpine runtime
- Non-root user
- Health checks

### .NET

- Multi-stage build with publish optimization
- ASP.NET runtime
- Non-root user
- Health checks

### Groovy

- Gradle-based builds
- Multi-stage optimization
- JRE runtime
- Health checks

### Robot Framework

- Optimized for test execution
- Xvfb support for GUI tests
- Results output directory

## Security Scanning

### Trivy

Trivy is enabled by default and scans for vulnerabilities in the Docker image.

Configure severity threshold in `config.yaml`:

```yaml
security:
  severity_threshold: HIGH  # CRITICAL, HIGH, MEDIUM, LOW
```

### Snyk

Enable Snyk scanning in `config.yaml`:

```yaml
snyk:
  enabled: true
```

Set Snyk token via environment variable:

```bash
export SNYK_TOKEN=your_snyk_token
```

## Image Signing

### Cosign (Default)

Cosign uses keyless signing by default. For key-based signing:

```yaml
signing:
  default_method: cosign
  cosign_key_path: /path/to/cosign/key.pem
```

### Docker Content Trust

Enable Docker Content Trust:

```yaml
signing:
  default_method: docker-trust
  docker_trust_passphrase: your_passphrase
```

## Registry Push

### DockerHub

Configure in `config.yaml`:

```yaml
dockerhub:
  username: your_username
  password: your_password_or_token
```

### Amazon ECR

Configure in `config.yaml`:

```yaml
ecr:
  repository_uri: 123456789012.dkr.ecr.us-east-1.amazonaws.com
  region: us-east-1
```

Ensure AWS CLI is configured with appropriate credentials.

## Notifications

### Slack

Enable Slack notifications:

```yaml
slack:
  enabled: true
  webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Email

Enable email notifications:

```yaml
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  username: your_email@gmail.com
  password: your_app_specific_password
  from_email: your_email@gmail.com
  to_emails:
    - recipient1@example.com
    - recipient2@example.com
```

## Metadata Storage

### Local Storage (Default)

Metadata is stored in the `metadata/` directory as JSON files.

### Amazon S3

Configure S3 storage:

```yaml
metadata_storage:
  type: s3

s3:
  bucket_name: your-bucket-name
  region: us-east-1
```

### Amazon DynamoDB

Configure DynamoDB storage:

```yaml
metadata_storage:
  type: dynamodb

dynamodb:
  table_name: your-table-name
  region: us-east-1
```

## Reports

HTML reports are generated in the `reports/` directory with:

- Build information (image name, tag, language, registry)
- Security scan summary with severity breakdown
- Detailed vulnerability table
- Pipeline status (signing, push)
- Timestamps

## Project Structure

```
Docker-image-factory-framework/
├── docker_image_factory.py      # Main framework script
├── config.yaml                   # Configuration file
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── modules/                      # Framework modules
│   ├── __init__.py
│   ├── config_loader.py          # Configuration loader
│   ├── dockerfile_generator.py   # Dockerfile generator
│   ├── security_scanner.py       # Security scanner (Trivy/Snyk)
│   ├── image_signer.py           # Image signer (Cosign/Docker Trust)
│   ├── registry_pusher.py        # Registry pusher (ECR/DockerHub)
│   ├── report_generator.py       # HTML report generator
│   ├── notification.py           # Notification manager (Slack/Email)
│   └── metadata_storage.py       # Metadata storage (S3/DynamoDB/Local)
├── templates/                    # Dockerfile templates (optional)
├── reports/                      # Generated HTML reports
├── logs/                         # Build logs
└── metadata/                     # Stored metadata files
```

## Examples

### Example 1: Python Application

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./my-python-app \
  --image-name my-python-app \
  --image-tag v1.0.0 \
  --custom-args '{"python_version": "3.11-slim", "port": 8000}'
```

### Example 2: Java Spring Boot Application

```bash
python docker_image_factory.py \
  --language java \
  --app-path ./my-spring-app \
  --image-name my-spring-app \
  --image-tag v2.0.0 \
  --custom-args '{"build_tool": "maven", "port": 8080}'
```

### Example 3: Node.js Application with ECR Push

```bash
python docker_image_factory.py \
  --language node \
  --app-path ./my-node-app \
  --image-name my-node-app \
  --registry ecr \
  --sign-method cosign
```

### Example 4: Go Application with Custom Base Image

```bash
python docker_image_factory.py \
  --language go \
  --app-path ./my-go-app \
  --image-name my-go-app \
  --base-image golang:1.21-alpine \
  --custom-args '{"port": 9090}'
```

## Troubleshooting

### Docker Build Fails

- Ensure Docker daemon is running
- Check that the app path is correct
- Verify that required files (e.g., requirements.txt, package.json) exist

### Security Scan Fails

- Ensure Trivy is installed: `trivy --version`
- Check that the image was built successfully
- Verify network connectivity for vulnerability database updates

### Image Signing Fails

- For Cosign keyless signing, ensure you're authenticated with GitHub/GitLab
- For key-based signing, verify the key path is correct
- For Docker Trust, ensure passphrase is set correctly

### Registry Push Fails

- Verify credentials are configured correctly
- For ECR, ensure AWS credentials are valid
- For DockerHub, ensure you have push permissions

### Notifications Not Sent

- Verify webhook URL or email settings
- Check network connectivity
- Review logs in the `logs/` directory

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions, please check the logs in the `logs/` directory or review the configuration in `config.yaml`.
