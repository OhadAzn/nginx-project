# End-to-End Explanation

This document explains everything in this project, from Docker basics to GitHub Actions CI. Written for someone who knows Jenkins but is new to GitHub Actions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Docker Concepts](#docker-concepts)
3. [The Nginx Container](#the-nginx-container)
4. [The Test Container](#the-test-container)
5. [Docker Compose](#docker-compose)
6. [GitHub Actions CI](#github-actions-ci)
7. [Jenkins vs GitHub Actions](#jenkins-vs-github-actions)
8. [How Everything Connects](#how-everything-connects)

---

## Project Overview

This project has two Docker containers:

1. **Nginx container**: A web server with two endpoints
2. **Test container**: A Python script that tests those endpoints

The CI pipeline builds both, runs them together, and reports pass/fail.
=



## The Nginx Container


**`FROM ubuntu:22.04`**
- Uses Ubuntu 22.04 as the base image
- The assignment requires Ubuntu (not Alpine or other distros)
- `22.04` is a specific version tag (LTS = Long Term Support)

**`ENV DEBIAN_FRONTEND=noninteractive`**
- Prevents apt from asking interactive questions during install
- Without this, the build might hang waiting for user input

**`RUN apt-get update && apt-get install -y ... && apt-get clean && rm -rf ...`**
- All in one `RUN` command (important for image size!)
- `apt-get update`: Refreshes package list
- `apt-get install -y`: Installs packages (-y = auto-yes to prompts)
- `--no-install-recommends`: Only install required packages, not "recommended" extras
- `apt-get clean` and `rm -rf /var/lib/apt/lists/*`: Removes cached package files

**Why one RUN command?**
Each `RUN` creates a new layer in the image. If you do:
```dockerfile
RUN apt-get update
RUN apt-get install nginx
RUN apt-get clean
```
The cached files from `apt-get update` are stored in the first layer and never truly deleted. Combining commands keeps the image smaller.

**`COPY nginx.conf /etc/nginx/nginx.conf`**
- Copies our custom nginx config into the image
- Replaces the default nginx configuration

**`COPY html/ /var/www/html/`**
- Copies the `html/` directory contents to nginx's web root
- This includes our `index.html`

**`EXPOSE 8080 8081`**
- Documents that this container uses ports 8080 and 8081
- This is just documentation - it doesn't actually open ports
- Ports are opened via docker-compose or `docker run -p`

**`HEALTHCHECK`**
- Tells Docker how to check if the container is healthy
- `--interval=10s`: Check every 10 seconds
- `--timeout=3s`: Wait max 3 seconds for response
- `--retries=3`: Mark unhealthy after 3 failures
- `CMD curl -f http://localhost:8080/ || exit 1`: The actual check command
- `-f` flag makes curl return non-zero exit code on HTTP errors

**`CMD ["nginx", "-g", "daemon off;"]`**
- The command to run when container starts
- `daemon off` keeps nginx in foreground (required for Docker)
- Docker expects the main process to stay in foreground
- If nginx daemonizes (goes to background), Docker thinks it exited

### File: `nginx/nginx.conf`

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /dev/stdout;
    error_log /dev/stderr;

    # Server 1: HTML response
    server {
        listen 8080;
        location / {
            root /var/www/html;
            index index.html;
        }
    }

    # Server 2: Error response
    server {
        listen 8081;
        location / {
            return 418 "I'm a teapot\n";
        }
    }
}
```

### Nginx Config Explanation

**`worker_processes auto;`**
- How many worker processes nginx spawns
- `auto` = match the number of CPU cores

**`events { worker_connections 1024; }`**
- Each worker can handle 1024 simultaneous connections
- For this test project, we'll never hit this limit

**`access_log /dev/stdout;` and `error_log /dev/stderr;`**
- Sends logs to stdout/stderr instead of files
- This is Docker best practice - lets you see logs with `docker logs`
- Also works with log aggregation systems

**`server { listen 8080; ... }`**
- First server block - listens on port 8080
- `root /var/www/html`: Serves files from this directory
- `index index.html`: Default file to serve

**`server { listen 8081; ... }`**
- Second server block - listens on port 8081
- `return 418 "I'm a teapot\n"`: Returns HTTP 418 status with message
- HTTP 418 is a real status code (RFC 2324) - a joke from April Fools 1998

### Why Two Ports Instead of Two Paths?

The assignment says "two Nginx server blocks" with "each server listens on a different port." We could have done:
- `http://nginx:8080/` for HTML
- `http://nginx:8080/error` for error

But the requirement specifically asks for different ports, so we use:
- `http://nginx:8080/` for HTML
- `http://nginx:8081/` for error

---

## The Test Container

### File: `tests/Dockerfile`

```dockerfile
FROM python:3.12-alpine
WORKDIR /app
COPY test.py .
CMD ["python", "test.py"]
```

### Line-by-Line Explanation

**`FROM python:3.12-alpine`**
- Uses Python 3.12 on Alpine Linux
- Alpine is a tiny Linux distro (~5MB vs ~70MB for Debian)
- `python:3.12-alpine` image is ~50MB vs ~900MB for `python:3.12`
- We can use Alpine here because the assignment only requires Ubuntu for nginx

**`WORKDIR /app`**
- Sets the working directory to `/app`
- All subsequent commands run from this directory
- If directory doesn't exist, it's created

**`COPY test.py .`**
- Copies `test.py` to `/app/test.py`
- The `.` means current directory (which is `/app` due to WORKDIR)

**`CMD ["python", "test.py"]`**
- Runs the test script when container starts

### File: `tests/test.py`

```python
import sys
import time
import urllib.request
import urllib.error

NGINX_HOST = "nginx"
MAX_RETRIES = 30

def wait_for_nginx():
    for i in range(MAX_RETRIES):
        try:
            urllib.request.urlopen(f"http://{NGINX_HOST}:8080/", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False

def test_html_endpoint():
    try:
        resp = urllib.request.urlopen(f"http://{NGINX_HOST}:8080/", timeout=5)
        body = resp.read().decode()
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        assert "Hello from Nginx" in body, "Missing expected content"
        print("Port 8080: PASS (200 OK)")
        return True
    except Exception as e:
        print(f"Port 8080: FAIL ({e})")
        return False

def test_error_endpoint():
    try:
        urllib.request.urlopen(f"http://{NGINX_HOST}:8081/", timeout=5)
        print("Port 8081: FAIL (expected error, got success)")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 418:
            print("Port 8081: PASS (418 I'm a teapot)")
            return True
        print(f"Port 8081: FAIL (expected 418, got {e.code})")
        return False
    except Exception as e:
        print(f"Port 8081: FAIL ({e})")
        return False

if __name__ == "__main__":
    print("Testing nginx endpoints...")
    if not wait_for_nginx():
        print("FAIL: nginx not ready")
        sys.exit(1)
    results = [test_html_endpoint(), test_error_endpoint()]
    if all(results):
        print("All tests passed")
        sys.exit(0)
    else:
        print("Some tests failed")
        sys.exit(1)
```

### Test Script Explanation

**Why `urllib` instead of `requests`?**
- `urllib` is part of Python standard library - no pip install needed
- Keeps the Docker image smaller
- `requests` would require: `RUN pip install requests`

**`NGINX_HOST = "nginx"`**
- In Docker Compose, containers can reach each other by service name
- Our nginx service is named "nginx" in docker-compose.yml
- So we connect to `http://nginx:8080/` not `http://localhost:8080/`

**`wait_for_nginx()` function**
- Containers start in parallel - nginx might not be ready when tests start
- This function retries up to 30 times (30 seconds) waiting for nginx
- Without this, tests would fail randomly due to timing

**Exit codes**
- `sys.exit(0)`: Success - all tests passed
- `sys.exit(1)`: Failure - one or more tests failed
- Docker Compose uses these to determine if the test container succeeded

**Testing HTTP 418**
- `urllib` raises `HTTPError` for non-2xx status codes
- We catch this exception and check if code is 418
- If we got 418, the test passes

---

## Docker Compose

### File: `docker-compose.yml`

```yaml
services:
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: nginx
    ports:
      - "8080:8080"
      - "8081:8081"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 5s

  tests:
    build:
      context: ./tests
      dockerfile: Dockerfile
    container_name: tests
    depends_on:
      nginx:
        condition: service_started
```

### Docker Compose Explanation

**What is Docker Compose?**
- A tool for defining multi-container applications
- Uses YAML file to configure services
- One command (`docker compose up`) starts everything

**`services:`**
- Defines the containers in this application
- Each service becomes a container

**`nginx:` service**
- `build.context: ./nginx`: Build image from `./nginx` directory
- `build.dockerfile: Dockerfile`: Use `Dockerfile` in that directory
- `container_name: nginx`: Name the container "nginx" (also the hostname)
- `ports: - "8080:8080"`: Map host port 8080 to container port 8080

**Port mapping format: `"HOST:CONTAINER"`**
- `"8080:8080"` means: host port 8080 → container port 8080
- You could do `"9000:8080"` to access on host port 9000
- The `ports` section is only for host access - containers can always reach each other

**`tests:` service**
- `depends_on.nginx.condition: service_started`: Wait for nginx container to start
- Note: "started" doesn't mean "ready" - that's why we have retry logic in Python

**Networking**
- Docker Compose creates a network automatically
- All services join this network
- Services can reach each other by name (e.g., `http://nginx:8080`)

### Running Docker Compose

```bash
# Build and run everything
docker compose up --build

# Run and exit when any container stops
docker compose up --build --abort-on-container-exit

# Exit with the exit code from tests container
docker compose up --build --abort-on-container-exit --exit-code-from tests

# Stop and remove containers
docker compose down

# Also remove volumes and orphan containers
docker compose down --volumes --remove-orphans
```

---

## GitHub Actions CI

### What is GitHub Actions?

GitHub Actions is GitHub's built-in CI/CD system. It runs workflows (pipelines) in response to events like pushes or pull requests.

**Key concepts:**
- **Workflow**: A YAML file defining the automation (like a Jenkinsfile)
- **Event**: What triggers the workflow (push, PR, schedule, etc.)
- **Job**: A set of steps that run on the same runner
- **Step**: Individual task (run a command, use an action)
- **Runner**: The machine that executes the job
- **Action**: Reusable unit of code (like Jenkins plugins)

### File: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build and run tests
        id: tests
        run: docker compose up --build --abort-on-container-exit --exit-code-from tests
        continue-on-error: true

      - name: Create result artifact
        run: |
          mkdir -p artifacts
          if [ "${{ steps.tests.outcome }}" == "success" ]; then
            touch artifacts/succeeded
          else
            touch artifacts/fail
          fi

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: artifacts/

      - name: Cleanup
        if: always()
        run: docker compose down --volumes --remove-orphans || true

      - name: Fail job if tests failed
        if: steps.tests.outcome == 'failure'
        run: exit 1
```

### Line-by-Line CI Explanation

**`name: CI`**
- Display name for this workflow in GitHub UI

**`on:` section (triggers)**
```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
```
- Workflow runs when:
  - Code is pushed to main or master branch
  - A pull request is opened/updated targeting main or master

**`jobs:` section**
- Defines the jobs to run
- Jobs run in parallel by default (we only have one job)

**`runs-on: ubuntu-latest`**
- Specifies the runner (machine) type
- `ubuntu-latest` is a GitHub-hosted runner with Ubuntu
- GitHub provides free runners with Docker pre-installed
- Other options: `windows-latest`, `macos-latest`, self-hosted runners

**Step 1: Checkout code**
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```
- `uses` means "use this action" (like a Jenkins plugin)
- `actions/checkout@v4` is GitHub's official action to clone your repo
- Without this, the runner has an empty workspace

**Step 2: Build and run tests**
```yaml
- name: Build and run tests
  id: tests
  run: docker compose up --build --abort-on-container-exit --exit-code-from tests
  continue-on-error: true
```
- `id: tests` gives this step an ID so we can reference it later
- `run` executes a shell command
- `continue-on-error: true` means: don't fail the whole job yet if this fails
- We need this to create the artifact before failing

**Step 3: Create result artifact**
```yaml
- name: Create result artifact
  run: |
    mkdir -p artifacts
    if [ "${{ steps.tests.outcome }}" == "success" ]; then
      touch artifacts/succeeded
    else
      touch artifacts/fail
    fi
```
- `${{ steps.tests.outcome }}` references the outcome of step with id "tests"
- Possible values: `success`, `failure`, `cancelled`, `skipped`
- Creates either `succeeded` or `fail` file as required by assignment

**Step 4: Upload artifact**
```yaml
- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: artifacts/
```
- `actions/upload-artifact@v4` is GitHub's action for uploading artifacts
- `with` provides parameters to the action
- Artifact named "test-results" will contain everything in `artifacts/`
- Artifacts are downloadable from the GitHub Actions UI

**Step 5: Cleanup**
```yaml
- name: Cleanup
  if: always()
  run: docker compose down --volumes --remove-orphans || true
```
- `if: always()` means: run this step even if previous steps failed
- Cleans up Docker resources
- `|| true` prevents failure if cleanup fails (containers might already be gone)

**Step 6: Fail job if tests failed**
```yaml
- name: Fail job if tests failed
  if: steps.tests.outcome == 'failure'
  run: exit 1
```
- Now that we've uploaded artifacts, we can fail the job
- `exit 1` makes the step fail, which fails the job
- This ensures the PR shows as failed

---

## Jenkins vs GitHub Actions

### Terminology Mapping

| Jenkins | GitHub Actions | Description |
|---------|---------------|-------------|
| Pipeline | Workflow | The automation definition |
| Jenkinsfile | `.github/workflows/*.yml` | The config file |
| Stage | Job | Group of related steps |
| Step | Step | Individual task |
| Agent/Node | Runner | Machine that runs the job |
| Plugin | Action | Reusable functionality |
| Build | Workflow Run | One execution |
| Artifact | Artifact | Files saved from a build |

### Configuration Comparison

**Jenkins (Declarative Pipeline):**
```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker compose build'
            }
        }
        stage('Test') {
            steps {
                sh 'docker compose up --abort-on-container-exit --exit-code-from tests'
            }
        }
    }
    post {
        always {
            sh 'docker compose down'
        }
    }
}
```

**GitHub Actions:**
```yaml
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
      - run: docker compose up --abort-on-container-exit --exit-code-from tests
      - if: always()
        run: docker compose down
```

### Key Differences

**1. Where it runs**
- Jenkins: Your own server (or cloud VM you manage)
- GitHub Actions: GitHub's servers (free tier available) or self-hosted runners

**2. Configuration location**
- Jenkins: Jenkinsfile (can be anywhere, usually repo root)
- GitHub Actions: Must be in `.github/workflows/` directory

**3. Trigger configuration**
- Jenkins: Configured in Jenkins UI or Jenkinsfile
- GitHub Actions: In the workflow YAML file (`on:` section)

**4. Secrets management**
- Jenkins: Credentials stored in Jenkins, accessed via `withCredentials`
- GitHub Actions: Secrets stored in GitHub, accessed via `${{ secrets.NAME }}`

**5. Plugins vs Actions**
- Jenkins: Plugins installed on Jenkins server, available to all pipelines
- GitHub Actions: Actions referenced per-workflow, from GitHub Marketplace or custom

**6. Syntax**
- Jenkins: Groovy-based DSL
- GitHub Actions: YAML

### Triggers Comparison

**Jenkins:**
```groovy
triggers {
    pollSCM('H/5 * * * *')  // Poll every 5 minutes
    cron('0 0 * * *')        // Daily at midnight
}
// Or webhooks configured in Jenkins UI
```

**GitHub Actions:**
```yaml
on:
  push:                      # On every push
    branches: [main]
  pull_request:              # On PR events
  schedule:
    - cron: '0 0 * * *'      # Daily at midnight
  workflow_dispatch:          # Manual trigger button
```

### Artifacts Comparison

**Jenkins:**
```groovy
post {
    always {
        archiveArtifacts artifacts: 'artifacts/**', fingerprint: true
    }
}
```

**GitHub Actions:**
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: my-artifact
    path: artifacts/
```

### Environment Variables

**Jenkins:**
```groovy
environment {
    MY_VAR = 'value'
    SECRET = credentials('my-secret-id')
}
```

**GitHub Actions:**
```yaml
env:
  MY_VAR: value
  SECRET: ${{ secrets.MY_SECRET }}
```

---

## How Everything Connects

### Local Development Flow

```
1. You edit files locally

2. Run: docker compose up --build --abort-on-container-exit --exit-code-from tests

3. Docker Compose:
   a. Builds nginx image from nginx/Dockerfile
   b. Builds tests image from tests/Dockerfile
   c. Creates a network
   d. Starts nginx container
   e. Starts tests container
   f. Tests container connects to http://nginx:8080 and http://nginx:8081
   g. Tests pass → exit code 0, tests fail → exit code 1
   h. Docker Compose exits with the tests exit code

4. You see results in terminal
```

### CI Flow (on git push)

```
1. You push to GitHub

2. GitHub detects push event

3. GitHub finds .github/workflows/ci.yml

4. GitHub starts a fresh Ubuntu VM (runner)

5. Runner executes workflow:
   a. Clone your repository
   b. Run docker compose (builds + runs containers)
   c. Capture test result (pass/fail)
   d. Create succeeded or fail file
   e. Upload as artifact
   f. Clean up containers
   g. Exit with appropriate code

6. GitHub shows result:
   - Green checkmark if passed
   - Red X if failed
   - Artifact available for download
```

### Network Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Host                               │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                Docker Compose Network                     │  │
│   │                    (f5_default)                           │  │
│   │                                                           │  │
│   │   ┌─────────────────┐       ┌─────────────────┐          │  │
│   │   │     nginx       │       │     tests       │          │  │
│   │   │                 │       │                 │          │  │
│   │   │   nginx:8080 ◄──────────│ Python script   │          │  │
│   │   │   nginx:8081 ◄──────────│                 │          │  │
│   │   │                 │       │                 │          │  │
│   │   └────────┬────────┘       └─────────────────┘          │  │
│   │            │                                              │  │
│   └────────────┼──────────────────────────────────────────────┘  │
│                │                                                  │
│       Port mapping (for local testing only)                      │
│                │                                                  │
│   ┌────────────▼────────┐                                        │
│   │   localhost:8080    │ ◄── You can curl this locally          │
│   │   localhost:8081    │                                        │
│   └─────────────────────┘                                        │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### File Relationship

```
.
├── .github/workflows/ci.yml    ─── Tells GitHub how to run CI
│
├── docker-compose.yml          ─── Orchestrates the containers
│       │
│       ├── builds ──► nginx/Dockerfile
│       │                   │
│       │                   └── copies ──► nginx/nginx.conf
│       │                   └── copies ──► nginx/html/index.html
│       │
│       └── builds ──► tests/Dockerfile
│                           │
│                           └── copies ──► tests/test.py
│
├── .dockerignore               ─── Files to exclude from Docker builds
│
└── README.md                   ─── Documentation
```

---

## Common Issues and Debugging

### Container can't reach nginx

**Problem:** `test.py` fails with connection refused

**Causes:**
1. Nginx not started yet → Solution: retry logic (we have this)
2. Wrong hostname → Must use service name "nginx", not "localhost"
3. Wrong port → Check nginx.conf matches test.py

**Debug:**
```bash
# See container logs
docker compose logs nginx
docker compose logs tests

# Shell into running container
docker compose exec nginx bash
docker compose exec tests sh

# Check if nginx is listening
docker compose exec nginx curl http://localhost:8080/
```

### Image build fails

**Problem:** Dockerfile fails during build

**Debug:**
```bash
# Build with more output
docker compose build --no-cache --progress=plain

# Build single service
docker compose build nginx
```

### GitHub Actions fails but works locally

**Possible causes:**
1. Different Docker version
2. Different OS (your Mac vs GitHub's Ubuntu)
3. Missing files not committed to git
4. Secrets not configured

**Debug:**
- Check the workflow run logs in GitHub UI
- Click on failed step to see output
- Add debug steps: `run: ls -la` to see files

---

## Summary

This project demonstrates:

1. **Docker fundamentals**: Building images, running containers
2. **Multi-container apps**: Docker Compose for orchestration
3. **Integration testing**: Container that tests another container
4. **CI/CD**: Automated builds and tests on every push
5. **Artifacts**: Saving and downloading build results

The pattern is common in real projects:
- Build your application container
- Build a test container
- Run them together
- Report results

This same pattern scales to much larger systems with databases, caches, message queues, and multiple microservices.
