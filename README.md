# DevOps Intern - Home Assignment

Two Docker containers: Nginx server with two endpoints, and a Python test container that verifies them.

## How to Run

```bash
docker compose up --build --abort-on-container-exit --exit-code-from tests
```

- Exit code 0 = tests passed
- Exit code 1 = tests failed

## What's Inside

**Nginx container** (Ubuntu-based):
- Port 8080: returns custom HTML page (HTTP 200)
- Port 8081: returns error response (HTTP 418)

**Test container** (Python Alpine):
- Sends requests to both nginx endpoints
- Verifies response codes and content
- Exits non-zero if any test fails

## Project Structure

```
.
├── nginx/
│   ├── Dockerfile      # Ubuntu + nginx
│   ├── nginx.conf      # Two server blocks
│   └── html/
│       └── index.html
├── tests/
│   ├── Dockerfile      # Python Alpine
│   └── test.py
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## CI/CD

GitHub Actions workflow (runs on `ubuntu-latest`):
1. Builds both Docker images
2. Runs `docker compose up`
3. Creates artifact with `succeeded` or `fail` file based on test result

## Design Notes

**Image sizes**: Nginx uses Ubuntu (required) but cleans apt cache. Tests use Python Alpine (~50MB).

**Port choice**: Using 8080/8081 instead of 80/443 since high ports work without root.

**Test retry**: Script waits up to 30 seconds for nginx to start before testing.

**No external deps**: Test script uses Python stdlib only (urllib).

## Manual Testing

```bash
# Start nginx only
docker compose up nginx --build -d

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8081/

# Cleanup
docker compose down
```
