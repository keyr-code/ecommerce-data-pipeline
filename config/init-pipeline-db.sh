#!/bin/bash
set -e

# Create pipeline_logs database and collections
mongosh <<EOF
use pipeline_logs

// Create collections with indexes
db.createCollection("logs")
db.createCollection("pipeline_runs")

// Create indexes for better query performance
db.logs.createIndex({ "run_id": 1 })
db.logs.createIndex({ "timestamp": -1 })
db.logs.createIndex({ "log_type": 1 })
db.logs.createIndex({ "filename": 1 })

db.pipeline_runs.createIndex({ "run_id": 1 }, { unique: true })
db.pipeline_runs.createIndex({ "start_time": -1 })

print("Pipeline logs database initialized successfully")
EOF