# Nginx on Ubuntu (required by assignment)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY html/ /var/www/html/

EXPOSE 8080 8081

CMD ["nginx", "-g", "daemon off;"]
