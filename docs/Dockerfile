# Dockerfile for Quantum-Enhanced Threat Scanner
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scanner/ ./scanner/
COPY models/ ./models/
COPY phase4/models/ ./phase4/models/
COPY utils/ ./utils/

# Create logs directory
RUN mkdir -p scanner/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
ENTRYPOINT ["python", "scanner/threat_scanner.py"]
CMD ["--help"]

# Usage examples:
# Build: docker build -t threat-scanner .
# Run:   docker run -it threat-scanner --domain example.com
# Shell: docker run -it threat-scanner /bin/bash
