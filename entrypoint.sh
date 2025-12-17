#!/bin/bash
set -e

# entrypoint.sh
# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Apply migrations
python manage.py migrate
python manage.py migrate precise_bbcode --database=archive
python manage.py migrate --database=archive
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput

# Start Daphne ASGI server
exec daphne -b 0.0.0.0 -p 8000 --proxy-headers utf.asgi:application