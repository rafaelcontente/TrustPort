FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for z3-solver compilation (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev,mcp]"

# Copy application code
COPY src/ ./src/
COPY mcp_server.py .
COPY examples/ ./examples/

# Set PYTHONPATH to ensure local imports work reliably
ENV PYTHONPATH=/app/src

# Expose API port
EXPOSE 8000

# Default command: run the API server
CMD ["uvicorn", "trust_net_port.api:app", "--host", "0.0.0.0", "--port", "8000"]
