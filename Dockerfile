FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY scripts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/init_db.py ./init_db.py

# Create directories for logs and database
RUN mkdir -p /app/pipeline_logs /app/database

# Initialize database on build
RUN python init_db.py

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017

# Default command
CMD ["python", "src/batch_load.py"]