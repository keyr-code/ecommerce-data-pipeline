#!/usr/bin/env python3
"""
Test script for data pipeline - local testing version
"""

import os
import sys
import pandas as pd

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_data_quality():
    """Test data quality validation"""
    print("🧪 TESTING DATA QUALITY")
    print("-" * 30)
    
    try:
        from data_quality_validator import DataQualityValidator
        from data_config import config_mapping
        
        data_files = ["customers.csv", "products.csv", "orders.csv", "order_items.csv", "raw_customers.csv","raw_customers_cleaned.csv"]
        results = {}
        
        for filename in data_files:
            # Read file (local path)
            df = pd.read_csv(f"data/{filename}")
            
            # Run validation
            validator = DataQualityValidator(df)
            validation_results = validator.run_all_checks(config_mapping[filename])
            
            results[filename] = {
                "passed": not validation_results['should_stop_pipeline'],
                "severity": validation_results['highest_severity'],
                "success_rate": validation_results['success_rate']
            }
            
            status = "✅ PASS" if results[filename]["passed"] else "❌ FAIL"
            print(f"{status} {filename}: {results[filename]['severity']} ({results[filename]['success_rate']:.1f}%)")
        
        return all(r["passed"] for r in results.values())
        
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        return False

def test_database():
    """Test database connection and schema"""
    print("\n🗄️  TESTING DATABASE")
    print("-" * 30)
    
    try:
        import duckdb
        
        # Use local database path
        conn = duckdb.connect("database/data_eng.db")
        
        # Check schema
        result = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ecommerce'").fetchone()
        if not result:
            print("❌ Schema 'ecommerce' not found")
            return False
        
        print("✅ Schema 'ecommerce' exists")
        
        # Check tables
        tables = ["customers", "products", "orders", "order_items", "raw_customers"]
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM ecommerce.{table}").fetchone()[0]
                print(f"✅ Table {table}: {count} rows")
            except Exception as e:
                print(f"❌ Table {table}: Error - {e}")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_imports():
    """Test that all modules can be imported"""
    print("\n📦 TESTING IMPORTS")
    print("-" * 30)
    
    modules = [
        "data_quality_validator",
        "data_config", 
        "batch_load",
        "reset_database",
        "pipeline_logger",
        "mongo_log_ingester"
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def test_config():
    """Test configuration files"""
    print("\n⚙️  TESTING CONFIGURATION")
    print("-" * 30)
    
    try:
        from data_config import config_mapping
        
        expected_files = ["customers.csv", "products.csv", "orders.csv", "order_items.csv", "raw_customers.csv"]
        
        for filename in expected_files:
            if filename in config_mapping:
                config = config_mapping[filename]
                print(f"✅ {filename}: {len(config.get('non_null_columns', []))} required columns")
            else:
                print(f"❌ {filename}: Missing configuration")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LOCAL PIPELINE TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Data Quality", test_data_quality),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n▶️  Running: {test_name}")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Pipeline is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check setup.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)