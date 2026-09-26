# Docker Image Factory Framework — Testing Guide

## Prerequisites Checklist

Before running any test, ensure the following are installed:

```bash
# Check Python
python3 --version

# Check Docker (must be running)
docker info

# Check Trivy (for security scan tests)
trivy --version

# Check Cosign (for signing tests, optional)
cosign version
```

Install Python dependencies:
```bash
cd Docker-image-factory-framework
pip install -r requirements.txt
```

---

## Scenario 1 — Python Flask App: Dockerfile Generation Only

**What it tests:** Generate the Dockerfile for a Python app WITHOUT building or pushing.

**Good for:** Verifying the template output before committing to a full build.

### Steps

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-test-app \
  --image-tag v1.0.0 \
  --skip-scan \
  --skip-sign \
  --skip-push
```

### What to check after running

```bash
# Verify Dockerfile was generated inside the app folder
cat ./test_apps/python_app/Dockerfile

# Verify build log was created
ls -lh logs/

# Verify metadata JSON was created locally
ls -lh metadata/
```

**Expected output:**
- `Dockerfile` created inside `test_apps/python_app/`
- Docker image `python-test-app:v1.0.0` listed in `docker images`
- Log file created under `logs/`

---

## Scenario 2 — Python App: Full Build + Trivy Security Scan

**What it tests:** Build the image AND run a Trivy vulnerability scan. Report is generated.

### Steps

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-test-app \
  --image-tag v1.0.0 \
  --skip-sign \
  --skip-push
```

### What to check after running

```bash
# Open the generated HTML report
open reports/build_report_python-test-app_*.html

# Inspect the Trivy scan output (also in logs)
cat logs/build_*.log | grep -A 5 "Trivy"

# Check vulnerability count in terminal output
```

**Expected output:**
- HTML report in `reports/` with severity breakdown (CRITICAL / HIGH / MEDIUM / LOW)
- Log file showing Trivy scan results
- If no Trivy installed: graceful error message in logs (not a crash)

---

## Scenario 3 — Python App: Custom Base Image

**What it tests:** Override the default `python:3.11-slim` with a custom base image.

### Steps

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-custom-base \
  --image-tag v1.0.0 \
  --base-image python:3.12-alpine \
  --skip-scan \
  --skip-sign \
  --skip-push
```

### What to check after running

```bash
# Check the FROM line in the generated Dockerfile
head -5 ./test_apps/python_app/Dockerfile
```

**Expected output:**
```dockerfile
FROM python:3.12-alpine AS builder
```

---

## Scenario 4 — Python App: Custom Port and Python Version via custom-args

**What it tests:** Pass custom arguments to override Dockerfile defaults.

### Steps

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-custom-args \
  --image-tag v1.0.0 \
  --custom-args '{"python_version": "3.12-slim", "port": "9090"}' \
  --skip-scan \
  --skip-sign \
  --skip-push
```

### What to check after running

```bash
# Check EXPOSE and base image in Dockerfile
grep -E "FROM|EXPOSE" ./test_apps/python_app/Dockerfile
```

**Expected output:**
```
FROM python:3.12-slim AS builder
EXPOSE 9090
```

---

## Scenario 5 — Robot Framework: Dockerfile Generation + Build

**What it tests:** Build a Docker image for a Robot Framework test suite.

### Steps

```bash
python docker_image_factory.py \
  --language robot \
  --app-path ./test_apps/robot_app \
  --image-name robot-test-suite \
  --image-tag v1.0.0 \
  --skip-scan \
  --skip-sign \
  --skip-push
```

### What to check after running

```bash
# Verify Dockerfile was generated for Robot Framework
cat ./test_apps/robot_app/Dockerfile

# Check the image exists in Docker
docker images | grep robot-test-suite
```

**Expected output in Dockerfile:**
```dockerfile
FROM python:3.11-slim AS builder
...
CMD ["robot", "--outputdir", "/app/results", "/app/tests"]
```

---

## Scenario 6 — Robot Framework: Run the Container and See Test Results

**What it tests:** Actually run the built Robot Framework container to execute tests.

### Steps

```bash
# Step 1: Build the Robot image (Scenario 5 above first)
python docker_image_factory.py \
  --language robot \
  --app-path ./test_apps/robot_app \
  --image-name robot-test-suite \
  --image-tag v1.0.0 \
  --skip-scan \
  --skip-sign \
  --skip-push

# Step 2: Run the Robot container with a mounted results folder
mkdir -p ./test_apps/robot_app/results

docker run --rm \
  -v "$(pwd)/test_apps/robot_app/results:/app/results" \
  robot-test-suite:v1.0.0

# Step 3: View the Robot Framework HTML report
open ./test_apps/robot_app/results/report.html
```

**Expected output:**
- Robot Framework test output in terminal
- `report.html`, `log.html`, `output.xml` created in `./test_apps/robot_app/results/`

---

## Scenario 7 — Python App: Full Pipeline (Build + Scan + Sign + Push to DockerHub)

**What it tests:** The entire pipeline end-to-end.

### Prerequisites

Configure DockerHub credentials in `.env` or `config.yaml`:
```yaml
dockerhub:
  username: your_dockerhub_username
  password: your_dockerhub_token
```

Or via environment variables:
```bash
export DOCKER_FACTORY_DOCKERHUB_USERNAME=your_username
export DOCKER_FACTORY_DOCKERHUB_PASSWORD=your_token
```

### Steps

```bash
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-test-app \
  --image-tag v1.0.0 \
  --registry dockerhub \
  --sign-method cosign
```

### What to check after running

```bash
# Verify HTML report was generated
open reports/build_report_python-test-app_*.html

# Verify image pushed to DockerHub (check your DockerHub dashboard)
# https://hub.docker.com/r/your_username/python-test-app

# Check metadata stored locally
cat metadata/metadata_python-test-app_*.json | python3 -m json.tool
```

---

## Scenario 8 — Verify Log Output

**What it tests:** That all pipeline stages are logged correctly.

### Steps

```bash
# Run any scenario, then inspect the log
python docker_image_factory.py \
  --language python \
  --app-path ./test_apps/python_app \
  --image-name python-log-test \
  --skip-scan --skip-sign --skip-push

# Read the latest log
cat $(ls -t logs/*.log | head -1)
```

**Expected log entries:**
```
INFO - Starting Docker Image Factory Pipeline
INFO - Generating Dockerfile for python
INFO - Dockerfile generated at ...
INFO - Building Docker image python-log-test:latest...
INFO - Docker image built successfully
INFO - Generating build report...
INFO - Report generated at reports/...
INFO - Storing build metadata...
INFO - Docker Image Factory Pipeline completed successfully
```

---

## Quick Reference: All CLI Flags

| Flag | Example | Purpose |
|---|---|---|
| `--language` | `python` / `robot` | Language to target |
| `--app-path` | `./test_apps/python_app` | Path to app source |
| `--image-name` | `my-app` | Docker image name |
| `--image-tag` | `v1.0.0` | Docker image tag |
| `--base-image` | `python:3.12-alpine` | Custom base image |
| `--custom-args` | `'{"port":"9090"}'` | JSON overrides |
| `--registry` | `dockerhub` / `ecr` | Push destination |
| `--sign-method` | `cosign` / `docker-trust` | Signing method |
| `--skip-scan` | — | Skip Trivy/Snyk |
| `--skip-sign` | — | Skip signing |
| `--skip-push` | — | Skip registry push |

---

## Test Folder Structure

```
test_apps/
├── python_app/
│   ├── main.py              # Flask web app
│   └── requirements.txt     # flask, gunicorn
└── robot_app/
    ├── requirements.txt     # robotframework, requests
    ├── tests/
    │   └── api_tests.robot  # Sample Robot Framework tests
    └── resources/
        └── common.resource  # Shared Robot keywords
```
