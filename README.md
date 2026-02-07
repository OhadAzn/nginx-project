# Project Overview

This project shows how to use Nginx as a secure web server (HTTPS) with DoS protection in a containerized environment. It also includes a CI/CD pipeline on GitHub that handles building, pushing, and running the project automatically.

## Main Components

**Nginx**: The web server. It uses port 8080 (HTTPS) for the main site and port 8081 for error testing.

**Docker**: We use Docker to package the code so it runs the same way on every machine. The Nginx image is based on Ubuntu as required.

**Docker Compose**: This tool manages the connection between the Nginx server and the test script. It lets you build and start everything with one command.

**Automated Testing**: A dedicated Test Container that runs a script to:
- Check Status: Verify that ports 8080 and 8081 return the correct status codes.
- Test Rate Limit: Simulate a "flood" of requests to verify that Nginx correctly blocks them.
- CI Integration: If any test fails, the GitHub pipeline stops automatically.

**CI Process**: Every time code is pushed to GitHub, a workflow starts. It builds the images, runs the tests, and uses Cosign to sign the images for security.

---

# Advanced 

**Generate OpenSSL Certificate**: Using HTTPS to allow Authentication and Authorization, which prevents Man-in-the-Middle attacks. Generating the cert inside the container environment to allow portability.

**DoS Defense**: Implemented rate limiting using Nginx to block DoS attacks, but making sure not to block when not needed and allowing bursts.

---

# Best Practices

We didn't just want it to work; we wanted it to follow professional DevOps standards:

**Multi-stage Dockerfile**: We used a two-stage build. The first stage prepares the files, and the second stage only contains the Nginx runtime. This keeps the final image small and secure because it doesn't include unnecessary build tools.
**Rate Limiting**: We configured Nginx to limit traffic to 5 requests per second per IP. This protects the server from being overwhelmed by too many requests.
**Image Signing (Cosign)**: Security is a priority. We sign our images in the CI pipeline so we can 
verify that the image running in production is exactly the one we built and tested.
**Environment Variables**: We used variables for the registry and image names, making the pipeline easy to update without changing the core code.
**Automated Cleanup**: The CI pipeline is designed to clean up after itself (Docker Compose down) and save test results as artifacts even if the build fails.

---

# How to use this project

### Local Setup

If you have Docker and Docker Compose installed, you can get everything running with one command:

```bash
docker compose up --build

```

### Accessing the Server

* **Main Site (HTML)**: Go to `http://localhost:8080`
* **Test Port (Text)**: Go to `http://localhost:8081`

### CI/CD Workflow

The automation is handled by GitHub Actions (found in `.github/workflows/ci.yml`). It follows these steps:

1. **Test**: Runs the containers and checks if they work.
2. **Build & Push**: If tests pass, it builds the production image and pushes it to GHCR.
3. **Sign**: Signs the image using a secure identity token.

---
