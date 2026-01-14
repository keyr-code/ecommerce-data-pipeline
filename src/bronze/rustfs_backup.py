"""
RustFS Backup Module

Backs up raw CSV data to RustFS (S3-compatible storage) for disaster recovery.
Supports concurrent uploads with error handling and logging.
"""

import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, Dict
import os
from src.common.logger import PipelineLogger


def initialize_s3_bucket(
    bucket_name: str = "ecommerce",
    endpoint_url: str = "http://localhost:9000",
    access_key: str = "rustfsadmin",
    secret_key: str = "rustfsadmin",
    logger: Optional[PipelineLogger] = None,
):
    """Initialize S3 resource and create bucket if needed"""
    s3 = boto3.resource(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    try:
        s3.create_bucket(Bucket=bucket_name)
        if logger:
            logger.log_database_operation(
                bucket_name, "CREATE_BUCKET", True, "Bucket created"
            )
    except Exception as e:
        if "BucketAlreadyOwnedByYou" not in str(e) and "BucketAlreadyExists" not in str(e):
            print(f"⚠ Bucket error: {e}")

    return s3.Bucket(bucket_name)


def upload_file(
    csv_file: Path, bucket, logger: PipelineLogger
) -> bool:
    """Upload single CSV file to RustFS"""
    try:
        with open(csv_file, "rb") as f:
            s3_key = f"backup/{csv_file.name}"
            bucket.put_object(Key=s3_key, Body=f.read())

        logger.log_database_operation(
            csv_file.name, f"UPLOAD_TO_RUSTFS:{s3_key}", True, "File uploaded"
        )
        return True

    except Exception as e:
        logger.log_database_operation(
            csv_file.name, "UPLOAD_TO_RUSTFS", False, str(e)
        )
        return False


def backup_directory(
    data_folder: Path, bucket, logger: PipelineLogger, max_workers: int = 5
) -> Dict[str, list]:
    """Backup all CSV files from directory using concurrent uploads"""
    csv_files = list(data_folder.glob("*.csv"))

    if not csv_files:
        return {"uploaded": [], "failed": []}

    uploaded = []
    failed = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(lambda f: upload_file(f, bucket, logger), csv_files)

        for csv_file, success in zip(csv_files, results):
            if success:
                uploaded.append(csv_file.name)
            else:
                failed.append(csv_file.name)

    return {"uploaded": uploaded, "failed": failed}


def backup_ecommerce_data(
    data_folder: Optional[Path] = None, max_workers: int = 5
) -> Tuple[Dict[str, list], PipelineLogger]:
    """Main backup function for e-commerce data"""
    logger = PipelineLogger()
    print(f"Backup run ID: {logger.run_id}")

    if data_folder is None:
        data_folder = Path(os.getenv("DATA_PATH", "/app/data"))

    bucket = initialize_s3_bucket(logger=logger)
    results = backup_directory(data_folder, bucket, logger, max_workers)

    return results, logger


if __name__ == "__main__":
    results, logger = backup_ecommerce_data(max_workers=5)

    print(f"\n📦 RUSTFS BACKUP RESULTS:")
    print(f"Uploaded: {results['uploaded']}")
    print(f"Failed: {results['failed']}")

    print(f"\n🆔 RUN ID: {logger.run_id}")
    print(f"📊 Query logs: python -m src.common.mongo_query run {logger.run_id}")
