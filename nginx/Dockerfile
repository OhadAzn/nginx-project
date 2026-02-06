# Multi-stage build: stage 1 prepares files, stage 2 runs nginx
# Base must be Ubuntu (assignment requirement)

# Stage 1: Prepare config files
FROM ubuntu:22.04 AS build
COPY nginx.conf /tmp/nginx.conf
COPY html/ /tmp/html/

# Stage 2: Runtime
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*
COPY --from=build /tmp/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /tmp/html/ /var/www/html/
EXPOSE 8080 8081
CMD ["nginx", "-g", "daemon off;"]
