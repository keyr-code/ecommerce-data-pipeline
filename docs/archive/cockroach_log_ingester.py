"""
CockroachDB Pipeline Log Ingestion System
"""

import psycopg2
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import re


class CockroachLogDB:
    """CockroachDB connection and log storage"""
    
    def __init__(self, connection_string: str = "postgresql://root@localhost:26257/pipeline_logs?sslmode=disable"):
        self.conn_string = connection_string
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize CockroachDB schema"""
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                # Create database if not exists
                cur.execute("CREATE DATABASE IF NOT EXISTS pipeline_logs")
                
        # Connect to the specific database
        db_conn_string = self.conn_string.replace("pipeline_logs?", "pipeline_logs/pipeline_logs?")
        
        with psycopg2.connect(db_conn_string) as conn:
            with conn.cursor() as cur:
                # Main logs table with JSONB
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        run_id STRING NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        log_type STRING NOT NULL,
                        filename STRING,
                        file_path STRING,
                        content JSONB,
                        raw_text TEXT,
                        ingested_at TIMESTAMPTZ DEFAULT now(),
                        INDEX idx_run_id (run_id),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_log_type (log_type),
                        INVERTED INDEX idx_content (content)
                    )
                """)
                
                # Pipeline runs summary table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        run_id STRING PRIMARY KEY,
                        start_time TIMESTAMPTZ,
                        end_time TIMESTAMPTZ,
                        duration_seconds DECIMAL,
                        status STRING,
                        success_rate DECIMAL,
                        total_files INT,
                        loaded_files INT,
                        skipped_files INT,
                        log_directory STRING,
                        metadata JSONB
                    )
                """)
    
    def store_log(self, log_data: Dict[str, Any]) -> None:
        """Store a single log entry"""
        db_conn_string = self.conn_string.replace("pipeline_logs?", "pipeline_logs/pipeline_logs?")
        
        with psycopg2.connect(db_conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO logs (run_id, timestamp, log_type, filename, file_path, content, raw_text)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    log_data['run_id'],
                    log_data['timestamp'],
                    log_data['log_type'],
                    log_data.get('filename'),
                    log_data.get('file_path'),
                    json.dumps(log_data.get('content', {})),
                    log_data.get('raw_text')
                ))
    
    def query_run_logs(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific run"""
        db_conn_string = self.conn_string.replace("pipeline_logs?", "pipeline_logs/pipeline_logs?")
        
        with psycopg2.connect(db_conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT run_id, timestamp, log_type, filename, content, raw_text
                    FROM logs 
                    WHERE run_id = %s 
                    ORDER BY timestamp
                """, (run_id,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def search_logs(self, search_term: str, days: int = 7) -> List[Dict[str, Any]]:
        """Full-text search across logs"""
        db_conn_string = self.conn_string.replace("pipeline_logs?", "pipeline_logs/pipeline_logs?")
        
        with psycopg2.connect(db_conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT run_id, timestamp, log_type, filename, raw_text
                    FROM logs 
                    WHERE raw_text ILIKE %s 
                    AND timestamp > now() - INTERVAL '%s days'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (f'%{search_term}%', days))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]


class LogFileParser:
    """Parse different types of log files"""
    
    @staticmethod
    def parse_validation_report(file_path: Path) -> Dict[str, Any]:
        """Parse dataset validation report"""
        content = file_path.read_text()
        
        # Extract key information using regex
        filename_match = re.search(r'Filename: (.+)', content)
        passed_match = re.search(r'Passed: (.+)', content)
        severity_match = re.search(r'Highest Severity: (.+)', content)
        success_rate_match = re.search(r'Success Rate: (.+)%', content)
        
        return {
            'log_type': 'validation_report',
            'filename': filename_match.group(1) if filename_match else None,
            'content': {
                'passed': passed_match.group(1) == 'True' if passed_match else None,
                'severity': severity_match.group(1) if severity_match else None,
                'success_rate': float(success_rate_match.group(1)) if success_rate_match else None,
                'validation_details': LogFileParser._extract_validation_results(content)
            },
            'raw_text': content
        }
    
    @staticmethod
    def parse_pipeline_summary(file_path: Path) -> Dict[str, Any]:
        """Parse pipeline summary"""
        content = file_path.read_text()
        
        # Extract summary information
        run_id_match = re.search(r'Run ID: (.+)', content)
        duration_match = re.search(r'Duration: (.+) seconds', content)
        success_rate_match = re.search(r'Success Rate: (.+)%', content)
        
        return {
            'log_type': 'pipeline_summary',
            'content': {
                'run_id': run_id_match.group(1) if run_id_match else None,
                'duration': float(duration_match.group(1)) if duration_match else None,
                'success_rate': float(success_rate_match.group(1)) if success_rate_match else None
            },
            'raw_text': content
        }
    
    @staticmethod
    def parse_application_log(file_path: Path) -> List[Dict[str, Any]]:
        """Parse Python logging output"""
        content = file_path.read_text()
        log_entries = []
        
        # Split by lines and parse each log entry
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
                
            # Parse log format: timestamp - level - message
            parts = line.split(' - ', 2)
            if len(parts) >= 3:
                log_entries.append({
                    'log_type': 'application_log',
                    'content': {
                        'timestamp': parts[0],
                        'level': parts[1],
                        'message': parts[2]
                    },
                    'raw_text': line
                })
        
        return log_entries
    
    @staticmethod
    def _extract_validation_results(content: str) -> List[Dict[str, str]]:
        """Extract individual validation check results"""
        results = []
        lines = content.split('\n')
        
        for line in lines:
            if '|' in line and ('PASS' in line or 'FAIL' in line):
                parts = line.split('|', 1)
                if len(parts) == 2:
                    status = parts[0].strip()
                    check_info = parts[1].strip()
                    
                    if ':' in check_info:
                        check_name, message = check_info.split(':', 1)
                        results.append({
                            'status': status,
                            'check_name': check_name.strip(),
                            'message': message.strip()
                        })
        
        return results


class PipelineLogIngester:
    """Main ingestion orchestrator"""
    
    def __init__(self, cockroach_db: CockroachLogDB):
        self.db = cockroach_db
        self.parser = LogFileParser()
    
    def ingest_run_directory(self, run_dir: Path) -> None:
        """Ingest all logs from a pipeline run directory"""
        run_id = run_dir.name
        
        # Process all log files
        for log_file in run_dir.rglob("*.txt"):
            self._ingest_file(run_id, log_file)
        
        for log_file in run_dir.rglob("*.log"):
            self._ingest_file(run_id, log_file)
    
    def _ingest_file(self, run_id: str, file_path: Path) -> None:
        """Ingest a single log file"""
        try:
            # Determine file type and parse accordingly
            if "validation" in file_path.name:
                log_data = self.parser.parse_validation_report(file_path)
                log_data.update({
                    'run_id': run_id,
                    'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'file_path': str(file_path)
                })
                self.db.store_log(log_data)
                
            elif "pipeline_summary" in file_path.name:
                log_data = self.parser.parse_pipeline_summary(file_path)
                log_data.update({
                    'run_id': run_id,
                    'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'file_path': str(file_path)
                })
                self.db.store_log(log_data)
                
            elif file_path.suffix == ".log":
                log_entries = self.parser.parse_application_log(file_path)
                for entry in log_entries:
                    entry.update({
                        'run_id': run_id,
                        'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'file_path': str(file_path)
                    })
                    self.db.store_log(entry)
                    
        except Exception as e:
            print(f"Error ingesting {file_path}: {e}")
    
    def ingest_all_runs(self, base_log_dir: str) -> None:
        """Ingest all pipeline runs from base directory"""
        base_path = Path(base_log_dir)
        
        for run_dir in base_path.iterdir():
            if run_dir.is_dir() and self._is_uuid(run_dir.name):
                print(f"Ingesting run: {run_dir.name}")
                self.ingest_run_directory(run_dir)
    
    def _is_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False


# Usage example
if __name__ == "__main__":
    # Initialize CockroachDB connection
    db = CockroachLogDB()
    
    # Create ingester
    ingester = PipelineLogIngester(db)
    
    # Ingest all existing logs
    ingester.ingest_all_runs("pipeline_logs")
    
    # Query examples
    print("Recent logs:", db.search_logs("CRITICAL", days=30))