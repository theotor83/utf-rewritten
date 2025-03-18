#!/bin/bash

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Waitress server
exec waitress-serve --port=8000 utf.wsgi:application