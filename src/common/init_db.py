#!/usr/bin/env python3
"""
Initialize DuckDB database and schema for Docker container
"""

import os
import sys
sys.path.append('/app/src')

from reset_database import reset_database

def init_database():
    """Initialize database with schema and tables"""
    print("🔧 Initializing DuckDB database...")
    
    # Ensure database directory exists
    db_path = os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    # Create database and tables
    reset_database()
    
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()