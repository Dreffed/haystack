FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY docker/backend/requirements.txt /app/requirements_backend.txt
COPY requirements.txt /app/requirements_base.txt
RUN pip install --no-cache-dir -r requirements_backend.txt -r requirements_base.txt

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/data/downloads /app/data/haystack /app/logs

# Set Python path
ENV PYTHONPATH=/app:/app/db:/app/engines

# Create non-root user for security
RUN groupadd -r haystack && useradd -r -g haystack haystack
RUN chown -R haystack:haystack /app
USER haystack

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "docker/backend/main.py"]