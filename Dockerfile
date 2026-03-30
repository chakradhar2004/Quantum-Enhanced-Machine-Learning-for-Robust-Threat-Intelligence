FROM python:3.10-slim

LABEL maintainer="Quantum-Enhanced Threat Intelligence"
LABEL description="Production-ready threat detection with classical + quantum ML"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py cli.py ./
COPY utils/ utils/
COPY scanner/ scanner/
COPY phase3/ phase3/
COPY phase4/ phase4/

# Copy models (these should be mounted as volumes in production)
# COPY models/ models/

# Create directories
RUN mkdir -p logs models data

# Set environment
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from config import PROJECT_ROOT; print('ok')" || exit 1

ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
