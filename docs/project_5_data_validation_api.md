# Project 5: Data Validation API Service

## Overview
Build a REST API service that provides data validation capabilities, combining all previous projects into a production-ready service.

## Skills You'll Learn
- FastAPI/Flask web development
- API design and documentation
- Async programming
- Database integration
- Docker containerization
- API testing and monitoring

## Implementation

```python
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import asyncio
import uuid
from datetime import datetime
import json
import io
from enum import Enum

# Pydantic models for API
class ValidationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ValidationRule(BaseModel):
    rule_type: str = Field(..., description="Type of validation rule")
    column: str = Field(..., description="Column to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    severity: ValidationSeverity = Field(default=ValidationSeverity.MEDIUM)
    enabled: bool = Field(default=True)

class ValidationRequest(BaseModel):
    data_format: str = Field(default="csv", description="Format of input data")
    validation_rules: List[ValidationRule] = Field(..., description="List of validation rules")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional options")

class ValidationResult(BaseModel):
    rule_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    failed_count: int = 0
    total_count: int = 0
    details: Optional[Dict[str, Any]] = None

class ValidationResponse(BaseModel):
    job_id: str
    status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    success_rate: float
    results: List[ValidationResult]
    processing_time_ms: int
    created_at: datetime

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None

# Data validation engine
class AsyncDataValidator:
    """Async data validation engine for API"""
    
    def __init__(self):
        self.validators = {
            'null_check': self._validate_nulls,
            'duplicate_check': self._validate_duplicates,
            'range_check': self._validate_range,
            'format_check': self._validate_format,
            'uniqueness_check': self._validate_uniqueness,
            'outlier_check': self._validate_outliers
        }
    
    async def validate_data(self, df: pd.DataFrame, rules: List[ValidationRule]) -> List[ValidationResult]:
        """Execute validation rules asynchronously"""
        results = []
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.rule_type in self.validators:
                try:
                    result = await self.validators[rule.rule_type](df, rule)
                    results.append(result)
                except Exception as e:
                    error_result = ValidationResult(
                        rule_name=f"{rule.rule_type}_{rule.column}",
                        passed=False,
                        severity=rule.severity,
                        message=f"Validation error: {str(e)}",
                        failed_count=1,
                        total_count=1
                    )
                    results.append(error_result)
        
        return results
    
    async def _validate_nulls(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate null values"""
        await asyncio.sleep(0.01)  # Simulate async processing
        
        if rule.column not in df.columns:
            raise ValueError(f"Column {rule.column} not found")
        
        null_count = df[rule.column].isnull().sum()
        max_nulls = rule.parameters.get('max_null_percentage', 0) / 100 * len(df)
        
        return ValidationResult(
            rule_name=f"null_check_{rule.column}",
            passed=null_count <= max_nulls,
            severity=rule.severity,
            message=f"Found {null_count} null values ({null_count/len(df)*100:.1f}%)",
            failed_count=null_count,
            total_count=len(df),
            details={"null_count": null_count, "threshold": rule.parameters.get('max_null_percentage', 0)}
        )
    
    async def _validate_duplicates(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate duplicate values"""
        await asyncio.sleep(0.01)
        
        columns = rule.parameters.get('columns', [rule.column])
        duplicate_count = df.duplicated(subset=columns).sum()
        
        return ValidationResult(
            rule_name=f"duplicate_check_{rule.column}",
            passed=duplicate_count == 0,
            severity=rule.severity,
            message=f"Found {duplicate_count} duplicate records",
            failed_count=duplicate_count,
            total_count=len(df),
            details={"duplicate_count": duplicate_count, "columns": columns}
        )
    
    async def _validate_range(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate numeric range"""
        await asyncio.sleep(0.01)
        
        if rule.column not in df.columns:
            raise ValueError(f"Column {rule.column} not found")
        
        numeric_data = pd.to_numeric(df[rule.column], errors='coerce')
        min_val = rule.parameters.get('min_value')
        max_val = rule.parameters.get('max_value')
        
        violations = 0
        if min_val is not None:
            violations += (numeric_data < min_val).sum()
        if max_val is not None:
            violations += (numeric_data > max_val).sum()
        
        return ValidationResult(
            rule_name=f"range_check_{rule.column}",
            passed=violations == 0,
            severity=rule.severity,
            message=f"Found {violations} range violations",
            failed_count=violations,
            total_count=len(df),
            details={"violations": violations, "min_value": min_val, "max_value": max_val}
        )
    
    async def _validate_format(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate string format"""
        await asyncio.sleep(0.01)
        
        import re
        
        if rule.column not in df.columns:
            raise ValueError(f"Column {rule.column} not found")
        
        pattern = rule.parameters.get('pattern')
        if not pattern:
            raise ValueError("No pattern specified for format validation")
        
        text_data = df[rule.column].dropna().astype(str)
        matches = text_data.str.match(pattern)
        violations = (~matches).sum()
        
        return ValidationResult(
            rule_name=f"format_check_{rule.column}",
            passed=violations == 0,
            severity=rule.severity,
            message=f"Found {violations} format violations",
            failed_count=violations,
            total_count=len(text_data),
            details={"violations": violations, "pattern": pattern}
        )
    
    async def _validate_uniqueness(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate column uniqueness"""
        await asyncio.sleep(0.01)
        
        if rule.column not in df.columns:
            raise ValueError(f"Column {rule.column} not found")
        
        duplicates = df[rule.column].duplicated().sum()
        
        return ValidationResult(
            rule_name=f"uniqueness_check_{rule.column}",
            passed=duplicates == 0,
            severity=rule.severity,
            message=f"Found {duplicates} duplicate values",
            failed_count=duplicates,
            total_count=len(df),
            details={"duplicate_count": duplicates, "unique_count": df[rule.column].nunique()}
        )
    
    async def _validate_outliers(self, df: pd.DataFrame, rule: ValidationRule) -> ValidationResult:
        """Validate statistical outliers"""
        await asyncio.sleep(0.01)
        
        if rule.column not in df.columns:
            raise ValueError(f"Column {rule.column} not found")
        
        numeric_data = pd.to_numeric(df[rule.column], errors='coerce').dropna()
        method = rule.parameters.get('method', 'iqr')
        threshold = rule.parameters.get('threshold', 1.5)
        
        if method == 'iqr':
            Q1 = numeric_data.quantile(0.25)
            Q3 = numeric_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outliers = ((numeric_data < lower_bound) | (numeric_data > upper_bound)).sum()
        else:
            outliers = 0
        
        return ValidationResult(
            rule_name=f"outlier_check_{rule.column}",
            passed=outliers == 0,
            severity=rule.severity,
            message=f"Found {outliers} statistical outliers",
            failed_count=outliers,
            total_count=len(numeric_data),
            details={"outlier_count": outliers, "method": method, "threshold": threshold}
        )

# Job management
class JobManager:
    """Manage validation jobs"""
    
    def __init__(self):
        self.jobs: Dict[str, JobStatus] = {}
        self.results: Dict[str, ValidationResponse] = {}
    
    def create_job(self) -> str:
        """Create new validation job"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = JobStatus(
            job_id=job_id,
            status="created",
            progress=0.0,
            message="Job created",
            created_at=datetime.now()
        )
        return job_id
    
    def update_job_status(self, job_id: str, status: str, progress: float, message: str):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            self.jobs[job_id].progress = progress
            self.jobs[job_id].message = message
            if status in ["completed", "failed"]:
                self.jobs[job_id].completed_at = datetime.now()
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def store_result(self, job_id: str, result: ValidationResponse):
        """Store validation result"""
        self.results[job_id] = result
    
    def get_result(self, job_id: str) -> Optional[ValidationResponse]:
        """Get validation result"""
        return self.results.get(job_id)

# FastAPI application
app = FastAPI(
    title="Data Validation API",
    description="REST API for comprehensive data validation",
    version="1.0.0"
)

# Global instances
validator = AsyncDataValidator()
job_manager = JobManager()

@app.get("/")
async def root():
    """API health check"""
    return {"message": "Data Validation API is running", "version": "1.0.0"}

@app.post("/validate", response_model=Dict[str, str])
async def validate_data(
    background_tasks: BackgroundTasks,
    request: ValidationRequest,
    file: UploadFile = File(...)
):
    """Submit data for validation"""
    
    # Create job
    job_id = job_manager.create_job()
    
    # Start background validation
    background_tasks.add_task(
        process_validation,
        job_id,
        file,
        request
    )
    
    return {"job_id": job_id, "status": "submitted"}

async def process_validation(job_id: str, file: UploadFile, request: ValidationRequest):
    """Process validation in background"""
    start_time = datetime.now()
    
    try:
        # Update job status
        job_manager.update_job_status(job_id, "processing", 10.0, "Loading data")
        
        # Load data
        content = await file.read()
        
        if request.data_format == "csv":
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif request.data_format == "json":
            df = pd.read_json(io.StringIO(content.decode('utf-8')))
        else:
            raise ValueError(f"Unsupported format: {request.data_format}")
        
        job_manager.update_job_status(job_id, "processing", 30.0, "Running validations")
        
        # Run validations
        results = await validator.validate_data(df, request.validation_rules)
        
        job_manager.update_job_status(job_id, "processing", 90.0, "Generating report")
        
        # Generate response
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        passed_checks = sum(1 for r in results if r.passed)
        
        response = ValidationResponse(
            job_id=job_id,
            status="completed",
            total_checks=len(results),
            passed_checks=passed_checks,
            failed_checks=len(results) - passed_checks,
            success_rate=(passed_checks / len(results) * 100) if results else 100,
            results=results,
            processing_time_ms=processing_time,
            created_at=start_time
        )
        
        # Store result
        job_manager.store_result(job_id, response)
        job_manager.update_job_status(job_id, "completed", 100.0, "Validation completed")
        
    except Exception as e:
        job_manager.update_job_status(job_id, "failed", 0.0, f"Error: {str(e)}")

@app.get("/jobs/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status"""
    status = job_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.get("/jobs/{job_id}/result", response_model=ValidationResponse)
async def get_validation_result(job_id: str):
    """Get validation result"""
    result = job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@app.get("/validation-rules")
async def get_available_rules():
    """Get list of available validation rules"""
    return {
        "rules": [
            {
                "rule_type": "null_check",
                "description": "Check for null/missing values",
                "parameters": {
                    "max_null_percentage": "Maximum allowed null percentage (0-100)"
                }
            },
            {
                "rule_type": "duplicate_check",
                "description": "Check for duplicate records",
                "parameters": {
                    "columns": "List of columns to check for duplicates"
                }
            },
            {
                "rule_type": "range_check",
                "description": "Check numeric values are within range",
                "parameters": {
                    "min_value": "Minimum allowed value",
                    "max_value": "Maximum allowed value"
                }
            },
            {
                "rule_type": "format_check",
                "description": "Check string format using regex",
                "parameters": {
                    "pattern": "Regular expression pattern"
                }
            },
            {
                "rule_type": "uniqueness_check",
                "description": "Check column values are unique",
                "parameters": {}
            },
            {
                "rule_type": "outlier_check",
                "description": "Check for statistical outliers",
                "parameters": {
                    "method": "Detection method (iqr, zscore)",
                    "threshold": "Threshold value"
                }
            }
        ]
    }

@app.post("/validate-sample")
async def validate_sample_data():
    """Validate sample data for testing"""
    # Create sample data
    sample_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['John', 'Jane', None, 'Mike', 'Sarah'],
        'age': [25, 30, 35, 200, 28],  # 200 is an outlier
        'email': ['john@test.com', 'jane@test.com', 'mike@test.com', 'invalid-email', 'sarah@test.com']
    })
    
    # Define validation rules
    rules = [
        ValidationRule(
            rule_type="null_check",
            column="name",
            parameters={"max_null_percentage": 10},
            severity=ValidationSeverity.HIGH
        ),
        ValidationRule(
            rule_type="range_check",
            column="age",
            parameters={"min_value": 0, "max_value": 120},
            severity=ValidationSeverity.MEDIUM
        ),
        ValidationRule(
            rule_type="format_check",
            column="email",
            parameters={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
            severity=ValidationSeverity.MEDIUM
        )
    ]
    
    # Run validation
    results = await validator.validate_data(sample_data, rules)
    
    passed_checks = sum(1 for r in results if r.passed)
    
    return {
        "total_checks": len(results),
        "passed_checks": passed_checks,
        "failed_checks": len(results) - passed_checks,
        "success_rate": (passed_checks / len(results) * 100) if results else 100,
        "results": [r.dict() for r in results]
    }

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    volumes:
      - ./logs:/app/logs
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: validation_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## API Testing Script

```python
import requests
import json
import time
import pandas as pd

# API client for testing
class ValidationAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def validate_file(self, file_path: str, rules: list) -> dict:
        """Submit file for validation"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'request': json.dumps({
                    'data_format': 'csv',
                    'validation_rules': rules
                })
            }
            response = requests.post(f"{self.base_url}/validate", files=files, data=data)
            return response.json()
    
    def get_job_status(self, job_id: str) -> dict:
        """Get job status"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}/status")
        return response.json()
    
    def get_result(self, job_id: str) -> dict:
        """Get validation result"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}/result")
        return response.json()
    
    def wait_for_completion(self, job_id: str, timeout: int = 60) -> dict:
        """Wait for job completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return self.get_result(job_id)
            elif status['status'] == 'failed':
                raise Exception(f"Job failed: {status['message']}")
            
            time.sleep(1)
        
        raise TimeoutError("Job did not complete within timeout")

# Example usage
if __name__ == "__main__":
    client = ValidationAPIClient()
    
    # Create test data
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['John', 'Jane', None, 'Mike', 'Sarah'],
        'age': [25, 30, 35, 200, 28],
        'email': ['john@test.com', 'jane@test.com', 'mike@test.com', 'invalid', 'sarah@test.com']
    })
    test_data.to_csv('test_data.csv', index=False)
    
    # Define validation rules
    rules = [
        {
            'rule_type': 'null_check',
            'column': 'name',
            'parameters': {'max_null_percentage': 10},
            'severity': 'high'
        },
        {
            'rule_type': 'range_check',
            'column': 'age',
            'parameters': {'min_value': 0, 'max_value': 120},
            'severity': 'medium'
        }
    ]
    
    # Submit validation
    job_response = client.validate_file('test_data.csv', rules)
    job_id = job_response['job_id']
    
    print(f"Job submitted: {job_id}")
    
    # Wait for completion
    result = client.wait_for_completion(job_id)
    
    print(f"Validation completed:")
    print(f"Success rate: {result['success_rate']:.1f}%")
    print(f"Total checks: {result['total_checks']}")
    print(f"Failed checks: {result['failed_checks']}")
```

## Your Task
1. Run the API service and test all endpoints
2. Add authentication and authorization
3. Implement rate limiting and request validation
4. Add database persistence for jobs and results
5. Create a web frontend for the API
6. Add monitoring and logging capabilities
7. Implement caching with Redis
8. Add API versioning and backward compatibility

## Key Concepts to Master
- REST API design principles
- Async programming with FastAPI
- Background task processing
- API documentation with OpenAPI/Swagger
- Error handling and status codes
- File upload and processing
- Database integration
- Containerization with Docker
- API testing and monitoring