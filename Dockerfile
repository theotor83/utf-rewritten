FROM python:3.11-slim

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
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install waitress psycopg2-binary

# Copy project files
COPY . /app/

# Make sure entrypoint script exists and has correct permissions
RUN ls -la /app/docker/entrypoint.sh || echo "ENTRYPOINT SCRIPT NOT FOUND"
RUN chmod +x /app/entrypoint.sh || echo "CHMOD FAILED"
RUN cp /app/docker/entrypoint.sh /app/ || echo "COPY FAILED"


# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]