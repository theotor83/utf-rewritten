#!/bin/sh

# Redis Docker entrypoint script for UTF-Rewritten Forum
# This script substitutes environment variables in the Redis configuration

set -e

# Check if REDIS_PASSWORD is set
if [ -z "$REDIS_PASSWORD" ]; then
    echo "ERROR: REDIS_PASSWORD environment variable is required but not set!"
    echo "Please set REDIS_PASSWORD in your .env file"
    exit 1
fi

# Create a temporary config file with password substitution
cp /usr/local/etc/redis/redis.conf /tmp/redis.conf
sed -i "s/\${REDIS_PASSWORD}/$REDIS_PASSWORD/g" /tmp/redis.conf

# Basic configuration validation (check if file exists and is readable)
if [ ! -r /tmp/redis.conf ]; then
    echo "ERROR: Redis configuration file is not readable"
    exit 1
fi

echo "Starting Redis with secure configuration..."
echo "Redis authentication: ENABLED"
echo "Protected mode: ENABLED"
echo "External ports: DISABLED (internal only)"

# Start Redis with the processed configuration
exec redis-server /tmp/redis.conf 