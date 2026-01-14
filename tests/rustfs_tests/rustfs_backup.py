"""
RustFS Backup Module

Backs up raw CSV data to RustFS (S3-compatible storage) for disaster recovery.
Supports concurrent uploads with error handling and logging.
"""

import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import os
from src.common.logger import PipelineLogger


class RustFSBackup:
    """Manages backup operations to RustFS storage"""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:9000",
        access_key: str = "rustfsadmin",
        secret_key: str = "rustfsadmin",
        bucket_name: str = "ecommerce",
        max_workers: int = 5,
    ):
        """
        Initialize RustFS backup client

        Args:
            endpoint_url: RustFS S3 API endpoint
            access_key: RustFS access key
            secret_key: RustFS secret key
            bucket_name: S3 bucket name for backups
            max_workers: Number of concurrent upload threads
        """
        self.s3 = boto3.resource(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.bucket_name = bucket_name
        self.max_workers = max_workers
        self.logger = PipelineLogger()
        self.bucket = self._initialize_bucket()

    def _initialize_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3.create_bucket(Bucket=self.bucket_name)
            self.logger.log_database_operation(
                self.bucket_name, "CREATE_BUCKET", True, "Bucket created"
            )
            print(f"✓ Created bucket: {self.bucket_name}")
        except Exception as e:
            if "BucketAlreadyOwnedByYou" in str(e) or "BucketAlreadyExists" in str(e):
                print(f"✓ Using existing bucket: {self.bucket_name}")
            else:
                print(f"⚠ Bucket error: {e}")
            return self.s3.Bucket(self.bucket_name)

        return self.s3.Bucket(self.bucket_name)

    def upload_file(self, csv_file: Path) -> bool:
        """
        Upload single CSV file to RustFS

        Args:
            csv_file: Path to CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(csv_file, "rb") as f:
                s3_key = f"backup/{csv_file.name}"
                self.bucket.put_object(Key=s3_key, Body=f.read())

            self.logger.log_database_operation(
                csv_file.name, f"UPLOAD_TO_RUSTFS:{s3_key}", True, "File uploaded"
            )
            print(f"✓ Uploaded {csv_file.name} → {s3_key}")
            return True

        except Exception as e:
            self.logger.log_database_operation(
                csv_file.name, f"UPLOAD_TO_RUSTFS", False, str(e)
            )
            print(f"✗ Error uploading {csv_file.name}: {e}")
            return False

    def backup_directory(self, data_folder: Path) -> dict:
        """
        Backup all CSV files from directory using concurrent uploads

        Args:
            data_folder: Path to folder containing CSV files

        Returns:
            Dictionary with upload results
        """
        csv_files = list(data_folder.glob("*.csv"))

        if not csv_files:
            print(f"⚠ No CSV files found in {data_folder}")
            return {"uploaded": [], "failed": []}

        print(f"\n📦 Starting backup of {len(csv_files)} files...")

        uploaded = []
        failed = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(self.upload_file, csv_files)

            for csv_file, success in zip(csv_files, results):
                if success:
                    uploaded.append(csv_file.name)
                else:
                    failed.append(csv_file.name)

        return {"uploaded": uploaded, "failed": failed}

    def print_summary(self, results: dict) -> None:
        """Print backup summary"""
        print("\n" + "=" * 60)
        print("RUSTFS BACKUP SUMMARY")
        print("=" * 60)
        print(f"✓ Uploaded: {len(results['uploaded'])} files")
        for file in results["uploaded"]:
            print(f"  • {file}")

        if results["failed"]:
            print(f"\n✗ Failed: {len(results['failed'])} files")
            for file in results["failed"]:
                print(f"  • {file}")

        print(f"\n🆔 Run ID: {self.logger.run_id}")
        print("=" * 60)


def backup_ecommerce_data(
    data_folder: Optional[Path] = None, max_workers: int = 5
) -> tuple:
    """
    Main backup function for e-commerce data

    Args:
        data_folder: Path to data folder (defaults to env DATA_PATH)
        max_workers: Number of concurrent upload threads

    Returns:
        Tuple of (results dict, logger instance)
    """
    if data_folder is None:
        data_folder = Path(os.getenv("DATA_PATH", "/app/data"))

    backup = RustFSBackup(max_workers=max_workers)
    results = backup.backup_directory(data_folder)
    backup.print_summary(results)

    return results, backup.logger


if __name__ == "__main__":
    from src.common.mongo_log_ingester import MongoLogDB

    results, logger = backup_ecommerce_data(max_workers=5)

    # Query and display backup logs
    if results["uploaded"]:
        print("\n📊 Querying backup logs from MongoDB...")
        try:
            db = MongoLogDB()
            logs = db.get_run_logs(logger.run_id)

            print(f"\n=== BACKUP LOGS FOR RUN {logger.run_id} ===")
            for log in logs:
                if "UPLOAD_TO_RUSTFS" in log.get("content", {}).get("operation", ""):
                    print(
                        f"✓ {log['content']['filename']}: {log['content']['operation']}"
                    )
        except Exception as e:
            print(f"⚠ Could not query logs: {e}")
