# Data Quality Validator Configuration Guide

## Basic Usage

```python
from data_quality_validator import DataQualityValidator
import pandas as pd

df = pd.read_csv('your_data.csv')
validator = DataQualityValidator(df)

config = {
    # Your configuration here
}

summary = validator.run_all_checks(config)
validator.print_detailed_summary()
```

## Configuration Options

### Completeness Checks

```python
config = {
    # Columns that cannot have null values (CRITICAL if violated)
    'non_null_columns': ['customer_id', 'email'],
    
    # Expected columns in dataset
    'expected_columns': ['id', 'name', 'email', 'age'],
    
    # Expected number of records
    'expected_record_count': 1000
}
```

### Data Type Validation

```python
config = {
    'type_mapping': {
        'customer_id': 'int',
        'age': 'int', 
        'price': 'float',
        'signup_date': 'datetime',
        'is_active': 'bool'
    }
}
```

### Format Validation (Regex)

```python
config = {
    'format_rules': {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\d{3}-\d{3}-\d{4}$',
        'zip_code': r'^\d{5}(-\d{4})?$'
    }
}
```

### Range Validation

```python
config = {
    'range_rules': {
        'age': (0, 120),
        'price': (0.01, 10000),
        'rating': (1, 5)
    }
}
```

### Domain Validation

```python
config = {
    'domain_rules': {
        'status': ['active', 'inactive', 'pending'],
        'category': ['A', 'B', 'C'],
        'country': ['US', 'CA', 'UK']
    }
}
```

### Uniqueness Checks

```python
config = {
    # Primary key (CRITICAL if duplicates found)
    'primary_key_columns': ['customer_id'],
    
    # Other unique columns (HIGH severity)
    'unique_columns': ['email', 'ssn']
}
```

### Business Logic Validation

```python
config = {
    'consistency_rules': [
        'start_date <= end_date',
        'discount_amount <= total_amount',
        'age >= 18'
    ]
}
```

## Complete Example

```python
config = {
    'non_null_columns': ['customer_id', 'email'],
    'expected_columns': ['customer_id', 'email', 'age', 'status', 'signup_date'],
    'type_mapping': {
        'customer_id': 'int',
        'age': 'int',
        'signup_date': 'datetime'
    },
    'format_rules': {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'range_rules': {
        'age': (13, 120)
    },
    'domain_rules': {
        'status': ['active', 'inactive', 'suspended']
    },
    'primary_key_columns': ['customer_id'],
    'unique_columns': ['email'],
    'consistency_rules': [
        'age >= 13'
    ]
}
```

## Severity Levels

- **CRITICAL**: Null values in non_null_columns, missing primary keys, type conversion failures
- **HIGH**: Uniqueness violations, significant record count differences  
- **MEDIUM**: Format violations, range violations, consistency rule failures
- **LOW**: Statistical outliers, successful validations

## Pipeline Integration

```python
# Check if data should stop pipeline
if validator.should_stop_pipeline(Severity.CRITICAL):
    print("❌ Critical issues found - stopping pipeline")
else:
    print("✅ Data quality acceptable - continuing pipeline")
```