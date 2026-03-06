# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py .

# Expose port (Cloud Run will use PORT env var)
EXPOSE 8080

# Health check - Cloud Run has built-in health checks, but keeping for local testing
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; import os; port=os.getenv('PORT', '8080'); httpx.get(f'http://localhost:{port}/health')"

# Run the application (Cloud Run will set PORT env var)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
