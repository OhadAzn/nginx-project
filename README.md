# Project Overview

This project is built around three main parts. The goal was to create a simple web server that is fully automated, easy to run, and secure from the start.

**Nginx**:
 Acts as the web server. It serves basic HTML on port 8080 and hard-coded text on port 8081.

**Docker**: 
We use containers to package the code. This makes it easy to run the project locally and ensures the CI process works exactly like our local environment.

**Docker Compose**: 
This is our orchestration tool. It lets us define the "desired state" of the app and run everything (build and start) with just one command.

**CI Process**:
 Every time code is pushed to GitHub, a workflow starts. it builds the image, runs tests, and uses **Cosign** to sign the image for security.

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

# Project Files

* **Dockerfile**: The multi-stage build configuration.
* **nginx.conf**: The server settings, including ports and rate limits.
* **docker-compose.yml**: The setup for local development and testing.
* **ci.yml**: The GitHub Actions logic.
