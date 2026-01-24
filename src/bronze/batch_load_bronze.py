"""
Bronze Layer Batch Load

Loads raw CSV data into bronze layer tables with raw_ prefix.
All data stored as VARCHAR (string) in bronze layer.
"""

import duckdb
from src.common.reset_database import clear_data_only
from src.common.logger import PipelineLogger
from typing import Dict, List, Any, Tuple
import os

data_csv = [
    "order_items.csv",
    "orders.csv",
    "products.csv",
    "raw_customers.csv",
    "customers.csv",
]

schema = "ecommerce"


def batch_load_bronze() -> Tuple[Dict[str, Any], PipelineLogger]:
    """Load raw CSV files into bronze layer"""
    logger = PipelineLogger()
    print(f"Bronze load run ID: {logger.run_id}")

    clear_data_only("bronze")
    logger.log_database_operation(
        "ALL_TABLES", "CLEAR DATA", True, rows_affected="All rows deleted"
    )

    conn = duckdb.connect(os.getenv("DUCKDB_PATH", "/app/database/data_eng.db"))
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    loaded_files: List[str] = []
    skipped_files: List[str] = []

    for data in data_csv:
        try:
            table_name = f"raw_{data.split('.')[0]}"
            data_path = os.path.join(os.getenv("DATA_PATH", "/app/data"), data)

            copy_command = f"COPY {schema}.{table_name} FROM '{data_path}' (FORMAT CSV, HEADER)"
            conn.execute(copy_command)

            result = conn.execute(
                f"SELECT COUNT(*) FROM {schema}.{table_name}"
            ).fetchone()
            row_count = result[0] if result else None

            logger.log_database_operation(
                data, f"COPY to {schema}.{table_name}", True, rows_affected=row_count
            )
            loaded_files.append(data)

        except Exception as e:
            logger.log_database_operation(data, "COPY to bronze", False, str(e))
            print(f"Load error for {data}: {e}")
            skipped_files.append(data)

    conn.close()

    results: Dict[str, Any] = {
        "loaded": loaded_files,
        "skipped": skipped_files,
    }
    logger.log_pipeline_results(results)

    return results, logger


if __name__ == "__main__":
    results, logger = batch_load_bronze()

    print(f"\n📦 BRONZE LOAD RESULTS:")
    print(f"Loaded files: {results['loaded']}")
    print(f"Skipped files: {results['skipped']}")

    print(f"\n🆔 RUN ID: {logger.run_id}")
    print(f"📊 Query logs: python -m src.common.mongo_query run {logger.run_id}")
