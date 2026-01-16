# Notification Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir psycopg2-binary

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/data \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8003

# Enhanced health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Set environment variables for production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application with proper error handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--log-level", "info"]