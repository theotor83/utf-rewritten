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

# Make sure entrypoint script has correct permissions
RUN chmod +x /app/docker/entrypoint.sh

# Run entrypoint script
ENTRYPOINT ["/app/docker/entrypoint.sh"]