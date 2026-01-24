import duckdb
from src.silver.data_quality_validator import DataQualityValidator, Severity
import pandas as pd
from src.silver.data_config import config_mapping
from src.common.reset_database import clear_data_only
from src.common.logger import PipelineLogger
from typing import Dict, List, Any, Tuple, Union, Optional
import os

bronze_tables = {
    "raw_customers": "customers",
    "raw_customers_v2": "clean_customers",
    "raw_orders": "orders",
    "_raw_order_items": "order_items",
    "raw_products": "products",
}

schema = "ecommerce"

def batch_load_data() -> Tuple[Dict[str, Any], PipelineLogger]:
    logger = PipelineLogger()
    print(f"Pipeline run ID: {logger.run_id}")

    clear_data_only("silver")
    logger.log_database_operation(
        "ALL_TABLES", "CLEAR DATA", True, rows_affected="All rows deleted"
    )

    file_results = quality_check(logger)

    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )

    loaded_tables: List[str] = []
    skipped_tables: List[str] = []

    for bronze_table, silver_table in bronze_tables.items():
        if file_results[bronze_table]["passed"]:
            try:
                copy_command = f"INSERT INTO {schema}.{silver_table} SELECT * FROM {schema}.{bronze_table}"
                conn.execute(copy_command)

                result = conn.execute(
                    f"SELECT COUNT(*) FROM {schema}.{silver_table}"
                ).fetchone()
                row_count = result[0] if result else None

                logger.log_database_operation(
                    bronze_table,
                    f"INSERT from {bronze_table} to {silver_table}",
                    True,
                    rows_affected=row_count,
                )
                loaded_tables.append(bronze_table)

            except Exception as e:
                logger.log_database_operation(
                    bronze_table, f"INSERT to {silver_table}", False, str(e)
                )
                print(f"Load error for {bronze_table}: {e}")
                skipped_tables.append(bronze_table)
        else:
            skipped_tables.append(
                f"{bronze_table} (quality issues: {file_results[bronze_table]['severity']})"
            )

    conn.close()

    pipeline_results: Dict[str, Any] = {
        "loaded": loaded_tables,
        "skipped": skipped_tables,
        "quality_results": file_results,
    }

    logger.log_pipeline_results(pipeline_results)

    return pipeline_results, logger


def quality_check(logger: PipelineLogger) -> Dict[str, Dict[str, Any]]:
    file_results: Dict[str, Dict[str, Any]] = {}

    for bronze_table in bronze_tables.keys():
        conn = duckdb.connect(
            os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
        )
        df = conn.execute(f"SELECT * FROM {schema}.{bronze_table}").df()
        conn.close()
        
        validator = DataQualityValidator(df)
        results = validator.run_all_checks(config_mapping.get(bronze_table, {}))

        file_results[bronze_table] = {
            "passed": not results["should_stop_pipeline"],
            "severity": results["highest_severity"],
            "critical_issues": [
                r
                for r in validator.results
                if r.severity == Severity.CRITICAL and not r.passed
            ],
        }

        logger.log_dataset_validation(bronze_table, results, validator)

    return file_results


if __name__ == "__main__":
    results, logger = batch_load_data()

    print(f"\n📊 BATCH LOAD RESULTS:")
    print(f"Loaded tables: {results['loaded']}")
    print(f"Skipped tables: {results['skipped']}")

    print(f"\n📋 QUALITY SUMMARY:")
    for table, quality in results["quality_results"].items():
        status = "✅" if quality["passed"] else "❌"
        print(f"{status} {table}: {quality['severity']} severity")

    print(f"\n🆔 RUN ID: {logger.run_id}")
    print(f"📊 Query logs: python -m src.common.mongo_query run {logger.run_id}")