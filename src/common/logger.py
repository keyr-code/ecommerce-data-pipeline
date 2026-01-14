from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import uuid
import logging
from src.common.mongo_log_ingester import MongoLogDB


class PipelineLogger:
    """Logger for pipeline runs with structured reports and operational logging"""

    def __init__(self) -> None:
        self.run_id: str = str(uuid.uuid4())
        self.pipeline_start_time: datetime = datetime.now()

        # Setup Python logging (console only)
        self.logger = logging.getLogger(f"pipeline.{self.run_id}")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Pipeline started - Run ID: {self.run_id}")
        
        # Initialize MongoDB connection
        try:
            self.mongo_db = MongoLogDB()
            self.mongo_enabled = True
            self.logger.info("MongoDB connection established")
        except Exception as e:
            self.mongo_enabled = False
            self.logger.error(f"MongoDB not available: {e}")
            raise Exception("MongoDB required for logging")
        
        # Store initial run data
        self.mongo_db.store_pipeline_run({
            "run_id": self.run_id,
            "start_time": self.pipeline_start_time,
            "status": "RUNNING",
            "ingested_at": datetime.now()
        })

    def log_dataset_validation(
        self, filename: str, validation_results: Dict[str, Any], validator: Any
    ) -> None:
        """Log dataset validation results to MongoDB"""
        
        # Console logging
        if validation_results['should_stop_pipeline']:
            self.logger.error(f"Validation FAILED for {filename}: {validation_results['highest_severity']} severity")
        else:
            self.logger.info(f"Validation PASSED for {filename}: {validation_results['success_rate']:.1f}% success rate")
        
        # Extract validation results
        validation_check_results = []
        for result in validator.results:
            validation_check_results.append({
                "status": "PASS" if result.passed else "FAIL",
                "check_name": result.check_name,
                "message": result.message
            })
        
        # Store in MongoDB
        mongo_doc = {
            "run_id": self.run_id,
            "log_type": "validation_report",
            "timestamp": datetime.now(),
            "filename": filename,
            "content": {
                "passed": not validation_results['should_stop_pipeline'],
                "severity": validation_results['highest_severity'],
                "success_rate": validation_results['success_rate'],
                "validation_results": validation_check_results
            },
            "raw_text": self._generate_validation_text(filename, validation_results, validator),
            "ingested_at": datetime.now()
        }
        
        self.mongo_db.store_log(mongo_doc)

    def log_pipeline_results(self, pipeline_results: Dict[str, Any]) -> Dict[str, Union[str, float]]:
        """Log pipeline results to MongoDB"""
        
        # Console logging
        total_files = len(pipeline_results['quality_results'])
        loaded_files = len(pipeline_results['loaded'])
        success_rate = (loaded_files / total_files * 100) if total_files > 0 else 0
        
        self.logger.info(f"Pipeline completed: {loaded_files}/{total_files} files loaded ({success_rate:.1f}% success)")
        
        if pipeline_results['skipped']:
            self.logger.warning(f"Skipped files: {pipeline_results['skipped']}")
        
        # Store pipeline summary in MongoDB
        mongo_doc = {
            "run_id": self.run_id,
            "log_type": "pipeline_summary",
            "timestamp": datetime.now(),
            "content": {
                "duration_seconds": (datetime.now() - self.pipeline_start_time).total_seconds(),
                "success_rate": success_rate,
                "total_files": total_files,
                "loaded_files": loaded_files
            },
            "raw_text": self._generate_pipeline_summary_text(pipeline_results),
            "ingested_at": datetime.now()
        }
        
        self.mongo_db.store_log(mongo_doc)
        
        # Update pipeline run metadata
        self.mongo_db.store_pipeline_run({
            "run_id": self.run_id,
            "start_time": self.pipeline_start_time,
            "duration_seconds": (datetime.now() - self.pipeline_start_time).total_seconds(),
            "success_rate": success_rate,
            "total_files": total_files,
            "loaded_files": loaded_files,
            "status": "COMPLETED",
            "ingested_at": datetime.now()
        })

        return {
            "run_id": self.run_id,
            "duration": (datetime.now() - self.pipeline_start_time).total_seconds(),
            "success_rate": success_rate,
        }

    def log_database_operation(
        self,
        filename: str,
        operation: str,
        success: bool,
        error_message: Optional[str] = None,
        rows_affected: Optional[Union[str, int]] = None,
    ) -> None:
        """Log database operations to MongoDB"""
        
        # Console logging
        if success:
            self.logger.info(f"Database operation SUCCESS: {operation} for {filename} ({rows_affected} rows)")
        else:
            self.logger.error(f"Database operation FAILED: {operation} for {filename} - {error_message}")
        
        # Store in MongoDB
        mongo_doc = {
            "run_id": self.run_id,
            "log_type": "database_operation",
            "timestamp": datetime.now(),
            "content": {
                "success": success,
                "filename": filename,
                "operation": operation,
                "rows_affected": str(rows_affected) if rows_affected is not None else None,
                "error_message": error_message
            },
            "raw_text": self._generate_db_operation_text(filename, operation, success, error_message, rows_affected),
            "ingested_at": datetime.now()
        }
        
        self.mongo_db.store_log(mongo_doc)

    def get_run_info(self) -> Dict[str, str]:
        """Get run information"""
        return {
            "run_id": self.run_id,
            "start_time": self.pipeline_start_time.isoformat(),
        }
    
    def _generate_validation_text(self, filename: str, validation_results: Dict[str, Any], validator: Any) -> str:
        """Generate validation report text in same format as file"""
        lines = []
        lines.append("Dataset Validation Report")
        lines.append("=" * 50)
        lines.append(f"Filename: {filename}")
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append(f"Passed: {not validation_results['should_stop_pipeline']}")
        lines.append(f"Highest Severity: {validation_results['highest_severity']}")
        lines.append(f"Success Rate: {validation_results['success_rate']:.1f}%")
        lines.append("")
        lines.append("Validation Results:")
        lines.append("-" * 30)
        
        for result in validator.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"{status} | {result.check_name}: {result.message}")
            
            if not result.passed and result.details:
                for key, value in result.details.items():
                    if isinstance(value, dict) and value:
                        lines.append(f"    {key}:")
                        for k, v in value.items():
                            lines.append(f"      {k}: {v}")
                    else:
                        lines.append(f"    {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_pipeline_summary_text(self, pipeline_results: Dict[str, Any]) -> str:
        """Generate pipeline summary text in same format as file"""
        lines = []
        lines.append("Pipeline Run Summary")
        lines.append("=" * 50)
        lines.append(f"Run ID: {self.run_id}")
        lines.append(f"Start Time: {self.pipeline_start_time.isoformat()}")
        lines.append(f"End Time: {datetime.now().isoformat()}")
        lines.append(f"Duration: {(datetime.now() - self.pipeline_start_time).total_seconds():.2f} seconds")
        lines.append("")
        lines.append("Results:")
        lines.append("-" * 20)
        lines.append(f"Total Files Processed: {len(pipeline_results['quality_results'])}")
        lines.append(f"Files Loaded: {len(pipeline_results['loaded'])}")
        lines.append(f"Files Skipped: {len(pipeline_results['skipped'])}")
        lines.append(f"Success Rate: {len(pipeline_results['loaded']) / len(pipeline_results['quality_results']) * 100:.1f}%")
        
        lines.append("")
        lines.append("Loaded Files:")
        for file in pipeline_results["loaded"]:
            lines.append(f"  ✓ {file}")
        
        lines.append("")
        lines.append("Skipped Files:")
        for file in pipeline_results["skipped"]:
            lines.append(f"  ✗ {file}")
        
        lines.append("")
        lines.append("Quality Summary:")
        lines.append("-" * 20)
        for filename, quality in pipeline_results["quality_results"].items():
            status = "PASS" if quality["passed"] else "FAIL"
            lines.append(f"{status} | {filename}: {quality['severity']} severity")
        
        return "\n".join(lines)
    
    def _generate_db_operation_text(self, filename: str, operation: str, success: bool, error_message: Optional[str], rows_affected: Optional[Union[str, int]]) -> str:
        """Generate database operation text in same format as file"""
        lines = []
        timestamp = datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILED"
        
        lines.append(f"[{timestamp}] {status}")
        lines.append(f"File: {filename}")
        lines.append(f"Operation: {operation}")
        
        if rows_affected is not None:
            lines.append(f"Rows Affected: {rows_affected}")
        
        if error_message:
            lines.append(f"Error: {error_message}")
        
        return "\n".join(lines)