"""
Pipeline Log Database Manager

Stores pipeline run metadata and results in SQLite for easy querying
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class PipelineLogDB:
    """Database manager for pipeline logs"""
    
    def __init__(self, db_path: str = "pipeline_logs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    success_rate REAL,
                    total_files INTEGER,
                    loaded_files INTEGER,
                    skipped_files INTEGER,
                    log_directory TEXT,
                    status TEXT DEFAULT 'RUNNING',
                    metadata JSON
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dataset_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    filename TEXT,
                    passed BOOLEAN,
                    severity TEXT,
                    success_rate REAL,
                    validation_results JSON,
                    FOREIGN KEY (run_id) REFERENCES pipeline_runs (run_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS database_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    filename TEXT,
                    operation TEXT,
                    success BOOLEAN,
                    rows_affected TEXT,
                    error_message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (run_id) REFERENCES pipeline_runs (run_id)
                )
            """)
    
    def store_pipeline_run(self, run_data: Dict[str, Any]) -> None:
        """Store pipeline run metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pipeline_runs 
                (run_id, start_time, end_time, duration_seconds, success_rate, 
                 total_files, loaded_files, skipped_files, log_directory, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_data['run_id'],
                run_data['start_time'],
                run_data.get('end_time'),
                run_data.get('duration_seconds'),
                run_data.get('success_rate'),
                run_data.get('total_files'),
                run_data.get('loaded_files'),
                run_data.get('skipped_files'),
                run_data['log_directory'],
                run_data.get('status', 'COMPLETED'),
                json.dumps(run_data.get('metadata', {}))
            ))
    
    def store_dataset_validation(self, run_id: str, filename: str, validation_data: Dict[str, Any]) -> None:
        """Store dataset validation results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO dataset_validations 
                (run_id, filename, passed, severity, success_rate, validation_results)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                filename,
                validation_data['passed'],
                validation_data['severity'],
                validation_data.get('success_rate'),
                json.dumps(validation_data)
            ))
    
    def store_database_operation(self, run_id: str, operation_data: Dict[str, Any]) -> None:
        """Store database operation results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO database_operations 
                (run_id, filename, operation, success, rows_affected, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                operation_data['filename'],
                operation_data['operation'],
                operation_data['success'],
                operation_data.get('rows_affected'),
                operation_data.get('error_message'),
                operation_data['timestamp']
            ))
    
    def get_pipeline_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get complete pipeline run information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get pipeline run
            run = conn.execute(
                "SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            
            if not run:
                return None
            
            # Get validations
            validations = conn.execute(
                "SELECT * FROM dataset_validations WHERE run_id = ?", (run_id,)
            ).fetchall()
            
            # Get database operations
            operations = conn.execute(
                "SELECT * FROM database_operations WHERE run_id = ?", (run_id,)
            ).fetchall()
            
            return {
                'pipeline_run': dict(run),
                'validations': [dict(v) for v in validations],
                'database_operations': [dict(op) for op in operations]
            }
    
    def query_runs(self, 
                   status: Optional[str] = None,
                   min_success_rate: Optional[float] = None,
                   start_date: Optional[str] = None,
                   limit: int = 50) -> List[Dict[str, Any]]:
        """Query pipeline runs with filters"""
        
        query = "SELECT * FROM pipeline_runs WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if min_success_rate is not None:
            query += " AND success_rate >= ?"
            params.append(min_success_rate)
        
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(query, params).fetchall()]
    
    def get_failed_validations(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get failed validations from last N days"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute("""
                SELECT dv.*, pr.start_time, pr.log_directory
                FROM dataset_validations dv
                JOIN pipeline_runs pr ON dv.run_id = pr.run_id
                WHERE dv.passed = 0 
                AND pr.start_time >= datetime('now', '-{} days')
                ORDER BY pr.start_time DESC
            """.format(days)).fetchall()]


# Usage example
if __name__ == "__main__":
    db = PipelineLogDB()
    
    # Example: Store a pipeline run
    run_data = {
        'run_id': 'e8e7f6a4-9822-4ef5-8af3-9bf95b46c102',
        'start_time': '2026-01-09T19:45:27.721461',
        'end_time': '2026-01-09T19:45:35.123456',
        'duration_seconds': 7.4,
        'success_rate': 80.0,
        'total_files': 5,
        'loaded_files': 4,
        'skipped_files': 1,
        'log_directory': '/path/to/logs/e8e7f6a4-9822-4ef5-8af3-9bf95b46c102',
        'status': 'COMPLETED'
    }
    
    db.store_pipeline_run(run_data)
    
    # Query examples
    print("Recent runs:", db.query_runs(limit=10))
    print("Failed validations:", db.get_failed_validations(days=30))
    print("Specific run:", db.get_pipeline_run('e8e7f6a4-9822-4ef5-8af3-9bf95b46c102'))