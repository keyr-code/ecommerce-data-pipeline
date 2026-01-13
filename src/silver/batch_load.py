import duckdb
from data_quality_validator import DataQualityValidator, Severity
import pandas as pd
from data_config import config_mapping
from reset_database import clear_data_only
from pipeline_logger import PipelineLogger
from typing import Dict, List, Any, Tuple, Union, Optional
import os

data_csv = [
    "order_items.csv",
    "orders.csv",
    "products.csv",
    "raw_customers.csv",
    "customers.csv",
]

schema = "ecommerce"

def batch_load_data() -> Tuple[Dict[str, Any], PipelineLogger]:
    # Initialize logger
    logger = PipelineLogger()
    print(f"Pipeline run ID: {logger.run_id}")

    # clear db
    clear_data_only()
    # Log database clearing operation
    logger.log_database_operation(
        "ALL_TABLES", "CLEAR DATA", True, rows_affected="All rows deleted"
    )

    # Check data quality first
    file_results = quality_check(logger)

    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )

    loaded_files: List[str] = []
    skipped_files: List[str] = []

    for data in data_csv:
        if file_results[data]["passed"]:
            try:
                table_name = data.split(".")[0]
                copy_command = f"COPY {schema}.{table_name} FROM '{os.getenv('DATA_PATH', '/app/data')}/{data}' (FORMAT CSV, HEADER)"

                conn.execute(copy_command)

                # Get row count for logging
                result = conn.execute(
                    f"SELECT COUNT(*) FROM {schema}.{table_name}"
                ).fetchone()
                row_count = result[0] if result else None

                logger.log_database_operation(
                    data,
                    f"COPY to {schema}.{table_name}",
                    True,
                    rows_affected=row_count,
                )
                loaded_files.append(data)

            except Exception as e:
                logger.log_database_operation(
                    data, f"COPY to {schema}.{data.split('.')[0]}", False, str(e)
                )
                print(f"Load error for {data}: {e}")
                skipped_files.append(data)
        else:
            skipped_files.append(
                f"{data} (quality issues: {file_results[data]['severity']})"
            )

    pipeline_results: Dict[str, Any] = {
        "loaded": loaded_files,
        "skipped": skipped_files,
        "quality_results": file_results,
    }

    # Log pipeline results
    pipeline_log = logger.log_pipeline_results(pipeline_results)

    return pipeline_results, logger


def quality_check(logger: PipelineLogger) -> Dict[str, Dict[str, Any]]:
    # Collect results for all files
    file_results: Dict[str, Dict[str, Any]] = {}

    for data in data_csv:
        df = pd.read_csv(
            os.getenv('DATA_PATH', '/app/data') + f'/{data}'
        )
        validator = DataQualityValidator(df)

        # Run validation
        results = validator.run_all_checks(config_mapping[data])

        # Store results for this file
        file_results[data] = {
            "passed": not results["should_stop_pipeline"],
            "severity": results["highest_severity"],
            "critical_issues": [
                r
                for r in validator.results
                if r.severity == Severity.CRITICAL and not r.passed
            ],
        }

        # Log individual dataset validation
        logger.log_dataset_validation(data, results, validator)

    return file_results


if __name__ == "__main__":
    results, logger = batch_load_data()

    print(f"\n📊 BATCH LOAD RESULTS:")
    print(f"Loaded files: {results['loaded']}")
    print(f"Skipped files: {results['skipped']}")

    print(f"\n📋 QUALITY SUMMARY:")
    for filename, quality in results["quality_results"].items():
        status = "✅" if quality["passed"] else "❌"
        print(f"{status} {filename}: {quality['severity']} severity")

    print(f"\n🆔 RUN ID: {logger.run_id}")
    print(f"📊 Query logs: python mongo_query.py run {logger.run_id}")