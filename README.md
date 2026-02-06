# DevOps Intern - Home Assignment

Two Docker containers: Nginx server with two endpoints (+ rate limiting), and a Python test container that verifies them.

## How to Run

```bash
docker compose up --build --abort-on-container-exit --exit-code-from tests
```

- Exit code 0 = tests passed
- Exit code 1 = tests failed

## What's Inside

**Nginx container** (Ubuntu-based):
- Port 8080: returns custom HTML page (HTTP 200) with rate limiting
- Port 8081: returns error response (HTTP 418)

**Test container** (Python Alpine):
- Sends requests to both nginx endpoints
- Verifies response codes and content
- Tests rate limiting (expects 429 when limit exceeded)
- Exits non-zero if any test fails

## Rate Limiting

Rate limiting is configured on port 8080 to prevent abuse.

**Current settings:**
- Rate: 5 requests per second per IP
- Burst: 10 requests (allows small spikes)
- Response: HTTP 429 when exceeded

**How it works:**
1. Nginx tracks each client IP address
2. Allows 5 requests per second sustained
3. Burst allows 10 extra requests to queue
4. After burst is exhausted, returns 429 Too Many Requests

**To change the rate limit**, edit `nginx/nginx.conf`:
```nginx
# Change rate (requests per second)
limit_req_zone $binary_remote_addr zone=limit:10m rate=10r/s;  # 10 req/s

# Change burst (spike allowance)
limit_req zone=limit burst=20 nodelay;  # Allow 20 burst
```

## Project Structure

```
.
├── nginx/
│   ├── Dockerfile      # Multi-stage, Ubuntu + nginx
│   ├── nginx.conf      # Two server blocks + rate limit
│   └── html/
│       └── index.html
├── tests/
│   ├── Dockerfile      # Python Alpine
│   └── test.py
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## CI/CD

GitHub Actions workflow:
1. Builds both Docker images
2. Runs tests via docker compose
3. Creates artifact (`succeeded` or `fail` file)
4. If tests pass: pushes nginx image to GitHub Container Registry
5. Signs image with cosign (keyless, using GitHub OIDC)

## Design Notes

**Multi-stage build**: Separates file preparation from runtime.

**Image sizes**: Nginx uses Ubuntu (required) but cleans apt cache. Tests use Python Alpine (~50MB).

**Rate limiting**: Protects against abuse, returns 429 when exceeded.

**Cosign**: Signs images using keyless signing (no keys to manage).

## Manual Testing

```bash
# Start nginx only
docker compose up nginx --build -d

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8081/

# Test rate limiting (run many times quickly)
for i in {1..20}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/; done

# Cleanup
docker compose down
```
