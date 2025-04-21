FROM nginx:1.27

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy the full nginx config (make sure it contains both HTTP and HTTPS blocks uncommented)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# CMD is inherited from base image (nginx -g 'daemon off;') and executed by entrypoint's exec