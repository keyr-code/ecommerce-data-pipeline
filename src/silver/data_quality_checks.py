from data_quality_validator import DataQualityValidator
import pandas as pd

# Load and inspect data
df = pd.read_csv(
    "/Users/kirenp/kiren2/projects_inprogress/2026_projects/Data Engineering Apprenticeship/Generated Sample Data/stage1_sample_data/raw_customers.csv"
)

# Create validator
validator = DataQualityValidator(df)

# Fixed configuration matching actual data structure
config = {
    "required_columns": ["customer_id", "name", "email", "country"],
    "non_null_columns": [
        "customer_id",
        "email",
    ],  # Only these columns must not have nulls
    "expected_columns": [
        "customer_id",
        "name",
        "email",
        "phone",
        "age",
        "country",
        "signup_date",
    ],
    "type_mapping": {
        "customer_id": "int",
        "name": "str",
        "email": "str",
        "phone": "str",
        "age": "int",
        "signup_date": "datetime",
    },
    "format_rules": {"email": r".*@.*"},
    "range_rules": {"customer_id": (1, 999999)},
    "primary_key_columns": ["customer_id"],
    "unique_columns": ["email"],
    "consistency_rules": ["customer_id > 0"],
}

# Run validation and get results
results = validator.run_all_checks(config)

# Use the built-in detailed summary method
validator.print_detailed_summary()

# Get pipeline decision from results
print(f"\n🔍 PIPELINE DECISION:")
print(f"Highest Severity: {results['highest_severity']}")
print(f"Should Stop Pipeline: {results['should_stop_pipeline']}")

if results["should_stop_pipeline"]:
    print("❌ STOPPING PIPELINE - Critical issues detected")
    exit(1)  # Exit with error code
else:
    print("✅ CONTINUING PIPELINE - No critical issues")