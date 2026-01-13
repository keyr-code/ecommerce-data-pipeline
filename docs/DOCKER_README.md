# Docker Setup for Data Pipeline

## Quick Start

```bash
# Start services
docker-compose up -d

# Initialize DuckDB (if needed)
docker-compose exec pipeline python init_db.py

# Run pipeline
docker-compose exec pipeline python src/batch_load.py

# Query logs
docker-compose exec pipeline python src/mongo_query.py list

# Stop services
docker-compose down
```

## Services

- **MongoDB**: Database on port 27017
- **Mongo Express**: Web UI on http://localhost:8081 (admin/admin)
- **Pipeline**: Data processing container

## Environment Variables

- `MONGO_HOST=mongodb`
- `MONGO_USERNAME=admin`
- `MONGO_PASSWORD=password123`
- `MONGO_DATABASE=pipeline_logs`

## Data Volumes

- `./src` → `/app/src` (source code)
- `./data` → `/app/data` (CSV files)
- `./pipeline_logs` → `/app/pipeline_logs` (logs)
- `./database` → `/app/database` (DuckDB files)