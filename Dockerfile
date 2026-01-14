FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY sql/ ./sql/
COPY config/ ./config/

# Create directories for logs, database, and data
RUN mkdir -p /app/pipeline_logs /app/database /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017
ENV DUCKDB_PATH=/app/database/data_eng.db
ENV DATA_PATH=/app/data

# Default command
CMD ["python", "-m", "src.silver.batch_load"]