# Project 3: Configuration Management System

## Overview
Build a flexible, configuration-driven data processing system that can be customized without code changes.

## Skills You'll Learn
- Configuration-driven design
- JSON/YAML handling
- Factory pattern
- Strategy pattern
- Validation frameworks

## Implementation

```python
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import pandas as pd

class ProcessingStrategy(Enum):
    CLEAN = "clean"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"

@dataclass
class ValidationRule:
    """Configuration for a single validation rule"""
    rule_type: str
    column: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"
    enabled: bool = True

@dataclass
class TransformationRule:
    """Configuration for a data transformation"""
    transform_type: str
    source_columns: List[str]
    target_column: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class ProcessingConfig:
    """Main configuration object for data processing"""
    name: str
    description: str
    input_format: str
    output_format: str
    validation_rules: List[ValidationRule] = field(default_factory=list)
    transformation_rules: List[TransformationRule] = field(default_factory=list)
    cleaning_rules: Dict[str, Any] = field(default_factory=dict)
    aggregation_rules: Dict[str, Any] = field(default_factory=dict)

class ConfigManager:
    """Manages loading and validation of processing configurations"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self, config_name: str) -> ProcessingConfig:
        """Load configuration from JSON or YAML file"""
        config_path = self.config_dir / f"{config_name}.json"
        yaml_path = self.config_dir / f"{config_name}.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        elif yaml_path.exists():
            with open(yaml_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Config file not found: {config_name}")
        
        return self._parse_config(config_data)
    
    def save_config(self, config: ProcessingConfig, filename: str, format: str = "json"):
        """Save configuration to file"""
        config_dict = self._config_to_dict(config)
        
        if format == "json":
            filepath = self.config_dir / f"{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
        elif format == "yaml":
            filepath = self.config_dir / f"{filename}.yaml"
            with open(filepath, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ProcessingConfig:
        """Parse dictionary into ProcessingConfig object"""
        validation_rules = [
            ValidationRule(**rule) for rule in config_data.get('validation_rules', [])
        ]
        
        transformation_rules = [
            TransformationRule(**rule) for rule in config_data.get('transformation_rules', [])
        ]
        
        return ProcessingConfig(
            name=config_data['name'],
            description=config_data.get('description', ''),
            input_format=config_data.get('input_format', 'csv'),
            output_format=config_data.get('output_format', 'csv'),
            validation_rules=validation_rules,
            transformation_rules=transformation_rules,
            cleaning_rules=config_data.get('cleaning_rules', {}),
            aggregation_rules=config_data.get('aggregation_rules', {})
        )
    
    def _config_to_dict(self, config: ProcessingConfig) -> Dict[str, Any]:
        """Convert ProcessingConfig to dictionary"""
        return {
            'name': config.name,
            'description': config.description,
            'input_format': config.input_format,
            'output_format': config.output_format,
            'validation_rules': [
                {
                    'rule_type': rule.rule_type,
                    'column': rule.column,
                    'parameters': rule.parameters,
                    'severity': rule.severity,
                    'enabled': rule.enabled
                } for rule in config.validation_rules
            ],
            'transformation_rules': [
                {
                    'transform_type': rule.transform_type,
                    'source_columns': rule.source_columns,
                    'target_column': rule.target_column,
                    'parameters': rule.parameters,
                    'enabled': rule.enabled
                } for rule in config.transformation_rules
            ],
            'cleaning_rules': config.cleaning_rules,
            'aggregation_rules': config.aggregation_rules
        }

class ValidationEngine:
    """Executes validation rules based on configuration"""
    
    def __init__(self):
        self.validators = {
            'null_check': self._validate_nulls,
            'range_check': self._validate_range,
            'format_check': self._validate_format,
            'uniqueness_check': self._validate_uniqueness
        }
    
    def execute_validations(self, df: pd.DataFrame, rules: List[ValidationRule]) -> Dict[str, Any]:
        """Execute all validation rules and return results"""
        results = {}
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.rule_type in self.validators:
                try:
                    result = self.validators[rule.rule_type](df, rule)
                    results[f"{rule.rule_type}_{rule.column}"] = result
                except Exception as e:
                    results[f"{rule.rule_type}_{rule.column}"] = {
                        'passed': False,
                        'error': str(e)
                    }
        
        return results
    
    def _validate_nulls(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Validate null values in column"""
        if rule.column not in df.columns:
            return {'passed': False, 'error': f'Column {rule.column} not found'}
        
        null_count = df[rule.column].isnull().sum()
        max_nulls = rule.parameters.get('max_null_percentage', 0) / 100 * len(df)
        
        return {
            'passed': null_count <= max_nulls,
            'null_count': null_count,
            'null_percentage': (null_count / len(df)) * 100,
            'threshold': rule.parameters.get('max_null_percentage', 0)
        }
    
    def _validate_range(self, df: pd.DataFrame, rule: ValidationResult) -> Dict[str, Any]:
        """Validate numeric range"""
        if rule.column not in df.columns:
            return {'passed': False, 'error': f'Column {rule.column} not found'}
        
        numeric_data = pd.to_numeric(df[rule.column], errors='coerce')
        min_val = rule.parameters.get('min_value')
        max_val = rule.parameters.get('max_value')
        
        violations = 0
        if min_val is not None:
            violations += (numeric_data < min_val).sum()
        if max_val is not None:
            violations += (numeric_data > max_val).sum()
        
        return {
            'passed': violations == 0,
            'violations': violations,
            'min_value': min_val,
            'max_value': max_val
        }
    
    def _validate_format(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Validate string format using regex"""
        import re
        
        if rule.column not in df.columns:
            return {'passed': False, 'error': f'Column {rule.column} not found'}
        
        pattern = rule.parameters.get('pattern')
        if not pattern:
            return {'passed': False, 'error': 'No pattern specified'}
        
        text_data = df[rule.column].dropna().astype(str)
        matches = text_data.str.match(pattern)
        violations = (~matches).sum()
        
        return {
            'passed': violations == 0,
            'violations': violations,
            'pattern': pattern,
            'match_rate': matches.mean() * 100
        }
    
    def _validate_uniqueness(self, df: pd.DataFrame, rule: ValidationRule) -> Dict[str, Any]:
        """Validate column uniqueness"""
        if rule.column not in df.columns:
            return {'passed': False, 'error': f'Column {rule.column} not found'}
        
        duplicates = df[rule.column].duplicated().sum()
        
        return {
            'passed': duplicates == 0,
            'duplicate_count': duplicates,
            'unique_count': df[rule.column].nunique(),
            'total_count': len(df)
        }

class TransformationEngine:
    """Executes transformation rules based on configuration"""
    
    def __init__(self):
        self.transformers = {
            'concatenate': self._concatenate_columns,
            'calculate': self._calculate_column,
            'extract_date_part': self._extract_date_part,
            'normalize': self._normalize_column
        }
    
    def execute_transformations(self, df: pd.DataFrame, rules: List[TransformationRule]) -> pd.DataFrame:
        """Execute all transformation rules"""
        result_df = df.copy()
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.transform_type in self.transformers:
                try:
                    result_df = self.transformers[rule.transform_type](result_df, rule)
                except Exception as e:
                    print(f"Transformation failed: {rule.transform_type} - {str(e)}")
        
        return result_df
    
    def _concatenate_columns(self, df: pd.DataFrame, rule: TransformationRule) -> pd.DataFrame:
        """Concatenate multiple columns"""
        separator = rule.parameters.get('separator', ' ')
        df[rule.target_column] = df[rule.source_columns].astype(str).agg(separator.join, axis=1)
        return df
    
    def _calculate_column(self, df: pd.DataFrame, rule: TransformationRule) -> pd.DataFrame:
        """Calculate new column using expression"""
        expression = rule.parameters.get('expression')
        if expression:
            df[rule.target_column] = df.eval(expression)
        return df
    
    def _extract_date_part(self, df: pd.DataFrame, rule: TransformationRule) -> pd.DataFrame:
        """Extract part of date (year, month, day, etc.)"""
        source_col = rule.source_columns[0]
        date_part = rule.parameters.get('date_part', 'year')
        
        date_series = pd.to_datetime(df[source_col])
        
        if date_part == 'year':
            df[rule.target_column] = date_series.dt.year
        elif date_part == 'month':
            df[rule.target_column] = date_series.dt.month
        elif date_part == 'day':
            df[rule.target_column] = date_series.dt.day
        elif date_part == 'weekday':
            df[rule.target_column] = date_series.dt.dayofweek
        
        return df
    
    def _normalize_column(self, df: pd.DataFrame, rule: TransformationRule) -> pd.DataFrame:
        """Normalize numeric column"""
        source_col = rule.source_columns[0]
        method = rule.parameters.get('method', 'minmax')
        
        if method == 'minmax':
            min_val = df[source_col].min()
            max_val = df[source_col].max()
            df[rule.target_column] = (df[source_col] - min_val) / (max_val - min_val)
        elif method == 'zscore':
            mean_val = df[source_col].mean()
            std_val = df[source_col].std()
            df[rule.target_column] = (df[source_col] - mean_val) / std_val
        
        return df

class ConfigurableProcessor:
    """Main processor that uses configuration to process data"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.validation_engine = ValidationEngine()
        self.transformation_engine = TransformationEngine()
    
    def process_data(self, df: pd.DataFrame, config_name: str) -> Dict[str, Any]:
        """Process data using specified configuration"""
        config = self.config_manager.load_config(config_name)
        
        results = {
            'config_name': config_name,
            'input_shape': df.shape,
            'validation_results': {},
            'transformation_applied': False,
            'output_shape': df.shape
        }
        
        # Execute validations
        if config.validation_rules:
            results['validation_results'] = self.validation_engine.execute_validations(
                df, config.validation_rules
            )
        
        # Execute transformations
        processed_df = df.copy()
        if config.transformation_rules:
            processed_df = self.transformation_engine.execute_transformations(
                processed_df, config.transformation_rules
            )
            results['transformation_applied'] = True
            results['output_shape'] = processed_df.shape
        
        results['processed_data'] = processed_df
        return results

# Example configuration creation
def create_sample_config():
    """Create a sample configuration"""
    config = ProcessingConfig(
        name="customer_data_processing",
        description="Process customer data with validation and transformations",
        input_format="csv",
        output_format="parquet",
        validation_rules=[
            ValidationRule(
                rule_type="null_check",
                column="customer_id",
                parameters={"max_null_percentage": 0},
                severity="critical"
            ),
            ValidationRule(
                rule_type="range_check",
                column="age",
                parameters={"min_value": 0, "max_value": 120},
                severity="high"
            ),
            ValidationRule(
                rule_type="format_check",
                column="email",
                parameters={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                severity="medium"
            )
        ],
        transformation_rules=[
            TransformationRule(
                transform_type="concatenate",
                source_columns=["first_name", "last_name"],
                target_column="full_name",
                parameters={"separator": " "}
            ),
            TransformationRule(
                transform_type="extract_date_part",
                source_columns=["signup_date"],
                target_column="signup_year",
                parameters={"date_part": "year"}
            )
        ]
    )
    
    return config

if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'first_name': ['John', 'Jane', 'Mike', 'Sarah', 'Tom'],
        'last_name': ['Doe', 'Smith', 'Johnson', 'Wilson', 'Brown'],
        'age': [25, 30, 35, 28, 45],
        'email': ['john@email.com', 'jane@email.com', 'mike@email.com', 'sarah@email.com', 'tom@email.com'],
        'signup_date': pd.date_range('2023-01-01', periods=5, freq='M')
    })
    
    # Create and save configuration
    config_manager = ConfigManager()
    sample_config = create_sample_config()
    config_manager.save_config(sample_config, "customer_processing")
    
    # Process data using configuration
    processor = ConfigurableProcessor(config_manager)
    results = processor.process_data(sample_data, "customer_processing")
    
    print("Processing Results:")
    print(f"Input shape: {results['input_shape']}")
    print(f"Output shape: {results['output_shape']}")
    print(f"Transformations applied: {results['transformation_applied']}")
    
    print("\nValidation Results:")
    for check, result in results['validation_results'].items():
        status = "✓" if result.get('passed', False) else "✗"
        print(f"{status} {check}: {result}")
    
    print("\nProcessed Data:")
    print(results['processed_data'])
```

## Your Task
1. Run this code and understand the configuration system
2. Add support for XML configuration files
3. Create a web interface to build configurations visually
4. Add configuration validation (ensure required fields are present)
5. Implement configuration versioning and rollback capabilities

## Key Concepts to Master
- Configuration-driven architecture
- Factory and Strategy patterns
- Serialization/deserialization (JSON, YAML)
- Dataclasses for structured configuration
- Flexible validation and transformation engines