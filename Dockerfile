# Dockerfile

FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=utf.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        postgresql-client \
        build-essential \
        netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip wheel \
    && pip install -r requirements.txt \
    && pip install waitress psycopg2-binary

# Copy project files
COPY . /app/

# Convert Windows line endings to Unix (in case of CRLF issues)
RUN apt-get update && apt-get install -y dos2unix

# Fix line endings and permissions for entrypoint script
RUN dos2unix /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && dos2unix /app/docker/redis/entrypoint.sh \
    && chmod +x /app/docker/redis/entrypoint.sh

# Run entrypoint script with explicit bash
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]