# Multi-stage build: stage 1 prepares files, stage 2 runs nginx

FROM ubuntu:22.04 AS build
COPY nginx.conf /tmp/nginx.conf
COPY html/ /tmp/html/

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx openssl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/server.key \
        -out /etc/nginx/ssl/server.crt \
        -subj "/CN=localhost"
COPY --from=build /tmp/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /tmp/html/ /var/www/html/
EXPOSE 8080 8081 443
CMD ["nginx", "-g", "daemon off;"]
