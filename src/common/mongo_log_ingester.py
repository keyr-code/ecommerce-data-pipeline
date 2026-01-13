"""
MongoDB Pipeline Log Ingestion System
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re
import uuid


class MongoLogDB:
    """MongoDB connection and log storage"""
    
    def __init__(self, connection_string: str = None, db_name: str = "pipeline_logs"):
        import os
        
        if connection_string is None:
            # Use environment variables for Docker
            mongo_host = os.getenv('MONGO_HOST', 'localhost')
            mongo_port = os.getenv('MONGO_PORT', '27017')
            mongo_username = os.getenv('MONGO_USERNAME')
            mongo_password = os.getenv('MONGO_PASSWORD')
            
            if mongo_username and mongo_password:
                connection_string = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/"
            else:
                connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.logs = self.db.logs
        self.runs = self.db.pipeline_runs
        self.init_indexes()
    
    def init_indexes(self) -> None:
        """Create indexes for efficient querying"""
        # Compound indexes for common queries
        self.logs.create_index([("run_id", ASCENDING), ("timestamp", DESCENDING)])
        self.logs.create_index([("log_type", ASCENDING), ("timestamp", DESCENDING)])
        self.logs.create_index([("timestamp", DESCENDING)])
        
        # Text index for full-text search
        self.logs.create_index([("raw_text", TEXT), ("content", TEXT)])
        
        # Pipeline runs indexes
        self.runs.create_index([("run_id", ASCENDING)], unique=True)
        self.runs.create_index([("start_time", DESCENDING)])
    
    def store_log(self, log_data: Dict[str, Any]) -> str:
        """Store a single log entry"""
        result = self.logs.insert_one(log_data)
        return str(result.inserted_id)
    
    def store_pipeline_run(self, run_data: Dict[str, Any]) -> None:
        """Store pipeline run metadata"""
        self.runs.replace_one(
            {"run_id": run_data["run_id"]}, 
            run_data, 
            upsert=True
        )
    
    def get_run_logs(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific run"""
        return list(self.logs.find(
            {"run_id": run_id}
        ).sort("timestamp", ASCENDING))
    
    def search_logs(self, search_term: str, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Full-text search across logs"""
        since_date = datetime.now() - timedelta(days=days)
        
        return list(self.logs.find({
            "$text": {"$search": search_term},
            "timestamp": {"$gte": since_date}
        }).sort("timestamp", DESCENDING).limit(limit))
    
    def get_failed_validations(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get failed validations from last N days"""
        since_date = datetime.now() - timedelta(days=days)
        
        return list(self.logs.find({
            "log_type": "validation_report",
            "content.passed": False,
            "timestamp": {"$gte": since_date}
        }).sort("timestamp", DESCENDING))
    
    def get_pipeline_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get pipeline statistics"""
        since_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"start_time": {"$gte": since_date}}},
            {"$group": {
                "_id": None,
                "total_runs": {"$sum": 1},
                "avg_success_rate": {"$avg": "$success_rate"},
                "avg_duration": {"$avg": "$duration_seconds"},
                "failed_runs": {"$sum": {"$cond": [{"$lt": ["$success_rate", 100]}, 1, 0]}}
            }}
        ]
        
        result = list(self.runs.aggregate(pipeline))
        return result[0] if result else {}


class LogFileParser:
    """Parse different types of log files into MongoDB documents"""
    
    @staticmethod
    def parse_validation_report(file_path: Path, run_id: str) -> Dict[str, Any]:
        """Parse dataset validation report"""
        content = file_path.read_text()
        
        # Extract metadata
        filename_match = re.search(r'Filename: (.+)', content)
        passed_match = re.search(r'Passed: (.+)', content)
        severity_match = re.search(r'Highest Severity: (.+)', content)
        success_rate_match = re.search(r'Success Rate: (.+)%', content)
        timestamp_match = re.search(r'Timestamp: (.+)', content)
        
        # Parse validation results
        validation_results = LogFileParser._extract_validation_results(content)
        
        return {
            "run_id": run_id,
            "log_type": "validation_report",
            "timestamp": datetime.fromisoformat(timestamp_match.group(1)) if timestamp_match else datetime.fromtimestamp(file_path.stat().st_mtime),
            "filename": filename_match.group(1) if filename_match else None,
            "file_path": str(file_path),
            "content": {
                "passed": passed_match.group(1) == 'True' if passed_match else None,
                "severity": severity_match.group(1) if severity_match else None,
                "success_rate": float(success_rate_match.group(1)) if success_rate_match else None,
                "validation_results": validation_results
            },
            "raw_text": content,
            "ingested_at": datetime.now()
        }
    
    @staticmethod
    def parse_pipeline_summary(file_path: Path, run_id: str) -> Dict[str, Any]:
        """Parse pipeline summary"""
        content = file_path.read_text()
        
        # Extract summary data
        duration_match = re.search(r'Duration: (.+) seconds', content)
        success_rate_match = re.search(r'Success Rate: (.+)%', content)
        total_files_match = re.search(r'Total Files Processed: (.+)', content)
        loaded_files_match = re.search(r'Files Loaded: (.+)', content)
        
        return {
            "run_id": run_id,
            "log_type": "pipeline_summary",
            "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime),
            "file_path": str(file_path),
            "content": {
                "duration_seconds": float(duration_match.group(1)) if duration_match else None,
                "success_rate": float(success_rate_match.group(1)) if success_rate_match else None,
                "total_files": int(total_files_match.group(1)) if total_files_match else None,
                "loaded_files": int(loaded_files_match.group(1)) if loaded_files_match else None
            },
            "raw_text": content,
            "ingested_at": datetime.now()
        }
    
    @staticmethod
    def parse_application_log(file_path: Path, run_id: str) -> List[Dict[str, Any]]:
        """Parse Python logging output into individual log entries"""
        content = file_path.read_text()
        log_entries = []
        
        for line_num, line in enumerate(content.strip().split('\n'), 1):
            if not line.strip():
                continue
            
            # Parse log format: timestamp - level - message
            parts = line.split(' - ', 2)
            if len(parts) >= 3:
                try:
                    timestamp = datetime.fromisoformat(parts[0])
                except:
                    timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                log_entries.append({
                    "run_id": run_id,
                    "log_type": "application_log",
                    "timestamp": timestamp,
                    "file_path": str(file_path),
                    "line_number": line_num,
                    "content": {
                        "level": parts[1],
                        "message": parts[2]
                    },
                    "raw_text": line,
                    "ingested_at": datetime.now()
                })
        
        return log_entries
    
    @staticmethod
    def parse_database_operations(file_path: Path, run_id: str) -> List[Dict[str, Any]]:
        """Parse database operations log"""
        content = file_path.read_text()
        operations = []
        
        # Split by operation blocks
        blocks = content.split('-' * 30)
        
        for block in blocks:
            if not block.strip() or 'Database Operations Log' in block:
                continue
            
            # Extract operation details
            timestamp_match = re.search(r'\[(.+?)\] (SUCCESS|FAILED)', block)
            file_match = re.search(r'File: (.+)', block)
            operation_match = re.search(r'Operation: (.+)', block)
            rows_match = re.search(r'Rows Affected: (.+)', block)
            error_match = re.search(r'Error: (.+)', block)
            
            if timestamp_match:
                try:
                    timestamp = datetime.fromisoformat(timestamp_match.group(1))
                except:
                    timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                operations.append({
                    "run_id": run_id,
                    "log_type": "database_operation",
                    "timestamp": timestamp,
                    "file_path": str(file_path),
                    "content": {
                        "success": timestamp_match.group(2) == 'SUCCESS',
                        "filename": file_match.group(1) if file_match else None,
                        "operation": operation_match.group(1) if operation_match else None,
                        "rows_affected": rows_match.group(1) if rows_match else None,
                        "error_message": error_match.group(1) if error_match else None
                    },
                    "raw_text": block.strip(),
                    "ingested_at": datetime.now()
                })
        
        return operations
    
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
                            "status": status,
                            "check_name": check_name.strip(),
                            "message": message.strip()
                        })
        
        return results


class PipelineLogIngester:
    """Main ingestion orchestrator for MongoDB"""
    
    def __init__(self, mongo_db: MongoLogDB):
        self.db = mongo_db
        self.parser = LogFileParser()
    
    def ingest_run_directory(self, run_dir: Path) -> None:
        """Ingest all logs from a pipeline run directory"""
        run_id = run_dir.name
        print(f"Ingesting run: {run_id}")
        
        # Track run metadata
        run_metadata = {
            "run_id": run_id,
            "log_directory": str(run_dir),
            "ingested_at": datetime.now(),
            "file_count": 0
        }
        
        # Process validation reports
        for validation_file in run_dir.glob("datasets/*_validation.txt"):
            log_doc = self.parser.parse_validation_report(validation_file, run_id)
            self.db.store_log(log_doc)
            run_metadata["file_count"] += 1
        
        # Process pipeline summary
        summary_file = run_dir / "pipeline_summary.txt"
        if summary_file.exists():
            log_doc = self.parser.parse_pipeline_summary(summary_file, run_id)
            self.db.store_log(log_doc)
            
            # Extract run metadata from summary
            if log_doc["content"]:
                run_metadata.update({
                    "duration_seconds": log_doc["content"].get("duration_seconds"),
                    "success_rate": log_doc["content"].get("success_rate"),
                    "total_files": log_doc["content"].get("total_files"),
                    "loaded_files": log_doc["content"].get("loaded_files")
                })
        
        # Process database operations
        db_ops_file = run_dir / "database_operations.txt"
        if db_ops_file.exists():
            operations = self.parser.parse_database_operations(db_ops_file, run_id)
            for op in operations:
                self.db.store_log(op)
        
        # Process application logs
        for log_file in run_dir.glob("*.log"):
            log_entries = self.parser.parse_application_log(log_file, run_id)
            for entry in log_entries:
                self.db.store_log(entry)
        
        # Store run metadata
        self.db.store_pipeline_run(run_metadata)
        print(f"✅ Ingested {run_metadata['file_count']} files for run {run_id}")
    
    def ingest_all_runs(self, base_log_dir: str) -> None:
        """Ingest all pipeline runs from base directory"""
        base_path = Path(base_log_dir)
        
        if not base_path.exists():
            print(f"Directory {base_log_dir} does not exist")
            return
        
        run_count = 0
        for run_dir in base_path.iterdir():
            if run_dir.is_dir() and self._is_uuid(run_dir.name):
                self.ingest_run_directory(run_dir)
                run_count += 1
        
        print(f"🎉 Completed ingestion of {run_count} pipeline runs")
    
    def _is_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False


# Usage example
if __name__ == "__main__":
    # Initialize MongoDB connection
    db = MongoLogDB()
    
    # Create ingester
    ingester = PipelineLogIngester(db)
    
    # Ingest all existing logs
    ingester.ingest_all_runs("pipeline_logs")
    
    # Query examples
    print("\n=== QUERY EXAMPLES ===")
    
    # Search for critical issues
    critical_logs = db.search_logs("CRITICAL", days=30)
    print(f"Found {len(critical_logs)} critical issues")
    
    # Get pipeline statistics
    stats = db.get_pipeline_stats(days=30)
    print(f"Pipeline stats: {stats}")
    
    # Get failed validations
    failures = db.get_failed_validations(days=7)
    print(f"Failed validations in last 7 days: {len(failures)}")