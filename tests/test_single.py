"""
Simple test runner for individual components
"""

import os
import sys

def test_single_file(filename):
    """Test validation for one CSV file"""
    import pandas as pd
    from data_quality_validator import DataQualityValidator
    from data_config import config_mapping
    
    print(f"Testing {filename}...")
    
    df = pd.read_csv(f"data/{filename}")
    validator = DataQualityValidator(df)
    results = validator.run_all_checks(config_mapping[filename])
    
    print(f"Rows: {len(df)}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Severity: {results['highest_severity']}")
    
    failed = [r for r in validator.results if not r.passed]
    if failed:
        print(f"Failed checks: {len(failed)}")
        for check in failed[:3]:
            print(f"  - {check.check_name}: {check.message}")

def test_database_reset():
    """Test database reset functionality"""
    from reset_database import reset_database
    
    print("Testing database reset...")
    reset_database()
    print("✅ Database reset completed")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tests/test_single.py <filename.csv>  # Test single file")
        print("  python tests/test_single.py reset           # Test database reset")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "reset":
        test_database_reset()
    elif arg.endswith(".csv"):
        test_single_file(arg)
    else:
        print(f"Unknown command: {arg}")
        sys.exit(1)