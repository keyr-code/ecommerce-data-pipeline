# CockroachDB Pipeline Log System

## Quick Setup

### 1. Install CockroachDB
```bash
# macOS
brew install cockroachdb/tap/cockroach

# Or download from https://www.cockroachlabs.com/docs/stable/install-cockroachdb-mac.html
```

### 2. Start CockroachDB (Single Node)
```bash
# Start single-node cluster
cockroach start-single-node --insecure --listen-addr=localhost:26257 --http-addr=localhost:8080

# In another terminal, create database
cockroach sql --insecure --execute="CREATE DATABASE IF NOT EXISTS pipeline_logs;"
```

### 3. Install Python Dependencies
```bash
pip install psycopg2-binary
```

### 4. Setup and Ingest Logs
```bash
# Setup database schema and ingest existing logs
python crdb_query.py setup
```

## Usage Examples

### Query Specific Run
```bash
python crdb_query.py run e8e7f6a4-9822-4ef5-8af3-9bf95b46c102
```

### Search Logs
```bash
# Search for CRITICAL issues in last 7 days
python crdb_query.py search "CRITICAL" --days 7

# Search for failed operations
python crdb_query.py search "FAILED" --days 30
```

### Ingest New Logs
```bash
python crdb_query.py ingest pipeline_logs/
```

## Advanced Queries (Direct SQL)

Connect to CockroachDB:
```bash
cockroach sql --insecure --database=pipeline_logs
```

### Example Queries
```sql
-- Get all validation failures by severity
SELECT run_id, filename, content->>'severity' as severity, timestamp
FROM logs 
WHERE log_type = 'validation_report' 
AND content->>'passed' = 'false'
ORDER BY timestamp DESC;

-- Count issues by type over time
SELECT 
    DATE_TRUNC('day', timestamp) as day,
    content->>'severity' as severity,
    COUNT(*) as issue_count
FROM logs 
WHERE log_type = 'validation_report'
AND content->>'passed' = 'false'
GROUP BY day, severity
ORDER BY day DESC;

-- Find runs with database operation failures
SELECT DISTINCT run_id, timestamp
FROM logs 
WHERE raw_text ILIKE '%database operation failed%'
ORDER BY timestamp DESC;

-- Search across all log content
SELECT run_id, log_type, filename, raw_text
FROM logs 
WHERE raw_text ILIKE '%your_search_term%'
ORDER BY timestamp DESC
LIMIT 50;
```

## Benefits of CockroachDB Approach

✅ **SQL + JSON**: Familiar SQL with flexible JSONB for log content  
✅ **Full-text search**: Search across all log content  
✅ **Scalable**: Can grow to multi-node cluster  
✅ **ACID transactions**: Data consistency guarantees  
✅ **Time-series queries**: Excellent for log analysis  
✅ **Inverted indexes**: Fast JSON queries  

## Web UI

CockroachDB provides a web interface at http://localhost:8080 for:
- Query execution
- Performance monitoring  
- Database metrics
- Cluster health

## Production Considerations

For production deployment:
- Use secure mode with certificates
- Set up multi-node cluster for high availability
- Configure backup and monitoring
- Use connection pooling for high-throughput ingestion