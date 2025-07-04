# docker/nginx/Dockerfile

FROM nginx:1.27

# Install dos2unix and Certbot for automatic SSL certificate renewal
RUN apt-get update && apt-get install -y \
    dos2unix \
    certbot \
    python3-certbot-nginx \
 && rm -rf /var/lib/apt/lists/*

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy the full nginx config (make sure it contains both HTTP and HTTPS blocks uncommented)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the entrypoint script and fix line endings
COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# CMD is inherited from base image (nginx -g 'daemon off;') and executed by entrypoint's exec