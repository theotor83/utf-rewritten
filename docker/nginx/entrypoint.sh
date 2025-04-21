#!/bin/sh
set -e

CONFIG_FILE="/etc/nginx/conf.d/default.conf"

if [ "$LOCALHOST_DOCKER" = "True" ]; then
    echo "Running in LOCALHOST_DOCKER mode."
    
    # Create a completely new nginx config from scratch
    cat > "$CONFIG_FILE" << EOF
upstream django {
    server web:8000;
}

# For local development without HTTPS
server {
    listen 80;
    server_name localhost;
    client_max_body_size 100M;
    
    location /static/ {
        alias /app/staticfiles/;
    }
    
    location /media/ {
        alias /app/media/;
    }
    
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # Fix for CSRF issues - ensure cookies are properly forwarded
        proxy_cookie_path / "/; HTTPOnly; Secure; SameSite=Lax";
    }
}
EOF
else
    echo "Running in production mode."
    
    # Create a production nginx config with HTTPS and HTTP->HTTPS redirect
    cat > "$CONFIG_FILE" << EOF
upstream django {
    server web:8000;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name utf-rewritten.org www.utf-rewritten.org;
    
    # Redirect all HTTP requests to HTTPS with a 301 Moved Permanently response
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl;
    server_name utf-rewritten.org www.utf-rewritten.org;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # File upload size
    client_max_body_size 100M;
    
    # Static and media files
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Main application
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # Fix for CSRF issues - ensure cookies are properly forwarded
        proxy_cookie_path / "/; HTTPOnly; Secure; SameSite=Lax";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

    # Ensure SSL directory exists
    mkdir -p /etc/nginx/ssl
fi

echo "Final Nginx configuration:"
cat "$CONFIG_FILE"
echo "---------------------------"

# Execute the original Nginx command
exec nginx -g 'daemon off;'