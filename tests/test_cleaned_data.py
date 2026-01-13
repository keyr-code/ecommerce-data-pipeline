
"""
Test full validation for raw_customers_cleaned.csv
"""

import os
import sys
import pandas as pd


from data_quality_validator import DataQualityValidator
from data_config import config_mapping

def test_raw_customers_cleaned():
    """Run full validation on raw_customers_cleaned.csv"""
    
    filename = "raw_customers_cleaned.csv"
    
    print(f"🔍 FULL VALIDATION: {filename}")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(f"data/{filename}"):
        print(f"❌ File not found: data/{filename}")
        return
    
    # Read the cleaned file
    df = pd.read_csv(f"data/{filename}")
    
    print(f"📊 Dataset Info:")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types:\n{df.dtypes}")
    
    # Use raw_customers config (since it's the cleaned version)
    config = config_mapping.get("raw_customers.csv", {})
    
    # Run validation
    validator = DataQualityValidator(df)
    results = validator.run_all_checks(config)
    
    print(f"\n📋 VALIDATION SUMMARY:")
    print(f"   Success Rate: {results['success_rate']:.1f}%")
    print(f"   Highest Severity: {results['highest_severity']}")
    print(f"   Should Stop Pipeline: {results['should_stop_pipeline']}")
    print(f"   Total Checks: {results['total_checks']}")
    print(f"   Passed Checks: {results['passed_checks']}")
    print(f"   Failed Checks: {results['failed_checks']}")
    
    # Show detailed results
    print(f"\n🔍 DETAILED RESULTS:")
    print("-" * 40)
    
    for result in validator.results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} {result.check_name}")
        print(f"    Severity: {result.severity}")
        print(f"    Message: {result.message}")
        
        if not result.passed and result.details:
            print(f"    Details:")
            for key, value in result.details.items():
                if isinstance(value, dict) and value:
                    print(f"      {key}:")
                    for k, v in list(value.items())[:5]:  # Show first 5
                        print(f"        {k}: {v}")
                    if len(value) > 5:
                        print(f"        ... and {len(value) - 5} more")
                else:
                    print(f"      {key}: {value}")
        print()
    
    # Show sample data
    print(f"📄 SAMPLE DATA (first 5 rows):")
    print(df.head())
    
    # Show data quality by column
    print(f"\n📊 COLUMN QUALITY:")
    print("-" * 30)
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        unique_count = df[col].nunique()
        print(f"{col}:")
        print(f"  Nulls: {null_count} ({null_pct:.1f}%)")
        print(f"  Unique: {unique_count}")
        print(f"  Type: {df[col].dtype}")
        
        # Show sample values
        sample_values = df[col].dropna().unique()[:3]
        print(f"  Sample: {list(sample_values)}")
        print()

if __name__ == "__main__":
    test_raw_customers_cleaned()