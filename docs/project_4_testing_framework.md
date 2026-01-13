# Project 4: Testing Framework for Data Validation

## Overview
Build a comprehensive testing framework for data validation with unit tests, integration tests, and test data generation.

## Skills You'll Learn
- Unit testing with pytest
- Test data generation
- Mocking and fixtures
- Test-driven development (TDD)
- Property-based testing

## Implementation

```python
import pytest
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass
import tempfile
import os

# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def create_clean_dataset(size: int = 100) -> pd.DataFrame:
        """Generate clean, valid test data"""
        np.random.seed(42)
        
        return pd.DataFrame({
            'id': range(1, size + 1),
            'name': [f'Person_{i}' for i in range(1, size + 1)],
            'age': np.random.randint(18, 80, size),
            'email': [f'person{i}@example.com' for i in range(1, size + 1)],
            'salary': np.random.normal(50000, 15000, size),
            'department': np.random.choice(['IT', 'HR', 'Finance', 'Marketing'], size),
            'hire_date': pd.date_range('2020-01-01', periods=size, freq='D')
        })
    
    @staticmethod
    def create_dirty_dataset(size: int = 100) -> pd.DataFrame:
        """Generate data with quality issues"""
        df = TestDataGenerator.create_clean_dataset(size)
        
        # Introduce nulls
        null_indices = np.random.choice(size, size // 10, replace=False)
        df.loc[null_indices, 'name'] = None
        
        # Introduce duplicates
        df.loc[size - 1] = df.loc[0]
        
        # Introduce invalid emails
        invalid_email_indices = np.random.choice(size, 5, replace=False)
        df.loc[invalid_email_indices, 'email'] = 'invalid-email'
        
        # Introduce outliers
        outlier_indices = np.random.choice(size, 3, replace=False)
        df.loc[outlier_indices, 'age'] = 200
        
        return df
    
    @staticmethod
    def create_edge_case_dataset() -> pd.DataFrame:
        """Generate edge cases for testing"""
        return pd.DataFrame({
            'empty_string': ['', 'valid', '', 'another'],
            'whitespace': ['  ', 'valid', '\t\n', 'another'],
            'mixed_types': [1, '2', 3.0, 'four'],
            'unicode': ['café', '北京', 'москва', 'normal'],
            'special_chars': ['@#$%', 'normal', '!@#$%^&*()', 'test'],
            'very_long_text': ['x' * 1000, 'short', 'y' * 5000, 'normal']
        })

# Mock data validator for testing
class MockDataValidator:
    """Mock validator for testing purposes"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = []
    
    def validate_nulls(self, column: str) -> Dict[str, Any]:
        """Mock null validation"""
        null_count = self.df[column].isnull().sum()
        return {
            'passed': null_count == 0,
            'null_count': null_count,
            'column': column
        }
    
    def validate_duplicates(self, columns: List[str]) -> Dict[str, Any]:
        """Mock duplicate validation"""
        duplicate_count = self.df.duplicated(subset=columns).sum()
        return {
            'passed': duplicate_count == 0,
            'duplicate_count': duplicate_count,
            'columns': columns
        }

# Test fixtures
@pytest.fixture
def clean_data():
    """Fixture providing clean test data"""
    return TestDataGenerator.create_clean_dataset(50)

@pytest.fixture
def dirty_data():
    """Fixture providing dirty test data"""
    return TestDataGenerator.create_dirty_dataset(50)

@pytest.fixture
def edge_case_data():
    """Fixture providing edge case test data"""
    return TestDataGenerator.create_edge_case_dataset()

@pytest.fixture
def temp_csv_file(clean_data):
    """Fixture providing temporary CSV file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        clean_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

# Unit tests for data validation
class TestDataValidation:
    """Unit tests for data validation functions"""
    
    def test_null_validation_clean_data(self, clean_data):
        """Test null validation with clean data"""
        validator = MockDataValidator(clean_data)
        result = validator.validate_nulls('name')
        
        assert result['passed'] is True
        assert result['null_count'] == 0
        assert result['column'] == 'name'
    
    def test_null_validation_dirty_data(self, dirty_data):
        """Test null validation with dirty data"""
        validator = MockDataValidator(dirty_data)
        result = validator.validate_nulls('name')
        
        assert result['passed'] is False
        assert result['null_count'] > 0
        assert result['column'] == 'name'
    
    def test_duplicate_validation_clean_data(self, clean_data):
        """Test duplicate validation with clean data"""
        validator = MockDataValidator(clean_data)
        result = validator.validate_duplicates(['id'])
        
        assert result['passed'] is True
        assert result['duplicate_count'] == 0
    
    def test_duplicate_validation_dirty_data(self, dirty_data):
        """Test duplicate validation with dirty data"""
        validator = MockDataValidator(dirty_data)
        result = validator.validate_duplicates(['id'])
        
        assert result['passed'] is False
        assert result['duplicate_count'] > 0
    
    def test_empty_dataframe(self):
        """Test validation with empty DataFrame"""
        empty_df = pd.DataFrame()
        validator = MockDataValidator(empty_df)
        
        with pytest.raises(KeyError):
            validator.validate_nulls('nonexistent_column')
    
    def test_single_row_dataframe(self):
        """Test validation with single row"""
        single_row_df = pd.DataFrame({'col1': [1], 'col2': ['test']})
        validator = MockDataValidator(single_row_df)
        result = validator.validate_nulls('col1')
        
        assert result['passed'] is True
        assert result['null_count'] == 0

# Integration tests
class TestDataProcessingPipeline:
    """Integration tests for complete data processing pipeline"""
    
    def test_end_to_end_processing(self, temp_csv_file):
        """Test complete pipeline from file to validation"""
        # Load data
        df = pd.read_csv(temp_csv_file)
        
        # Process data
        validator = MockDataValidator(df)
        
        # Run validations
        null_result = validator.validate_nulls('name')
        duplicate_result = validator.validate_duplicates(['id'])
        
        # Assert results
        assert null_result['passed'] is True
        assert duplicate_result['passed'] is True
        assert len(df) > 0
    
    def test_pipeline_with_transformations(self, clean_data):
        """Test pipeline including data transformations"""
        # Apply transformation
        clean_data['full_name'] = clean_data['name'] + '_transformed'
        
        # Validate transformation
        assert 'full_name' in clean_data.columns
        assert all(clean_data['full_name'].str.endswith('_transformed'))
        
        # Run validation on transformed data
        validator = MockDataValidator(clean_data)
        result = validator.validate_nulls('full_name')
        assert result['passed'] is True

# Property-based testing
class TestDataProperties:
    """Property-based tests for data validation"""
    
    def test_data_consistency_properties(self, clean_data):
        """Test that data maintains consistent properties"""
        # Property: All IDs should be unique
        assert clean_data['id'].nunique() == len(clean_data)
        
        # Property: Ages should be reasonable
        assert clean_data['age'].min() >= 0
        assert clean_data['age'].max() <= 150
        
        # Property: Emails should contain @ symbol
        valid_emails = clean_data['email'].str.contains('@', na=False)
        assert valid_emails.all()
    
    def test_data_type_consistency(self, clean_data):
        """Test data type consistency"""
        # Property: Numeric columns should be numeric
        assert pd.api.types.is_numeric_dtype(clean_data['age'])
        assert pd.api.types.is_numeric_dtype(clean_data['salary'])
        
        # Property: Date columns should be datetime
        assert pd.api.types.is_datetime64_any_dtype(clean_data['hire_date'])

# Performance tests
class TestDataValidationPerformance:
    """Performance tests for data validation"""
    
    def test_validation_performance_large_dataset(self):
        """Test validation performance with large dataset"""
        import time
        
        # Create large dataset
        large_data = TestDataGenerator.create_clean_dataset(10000)
        
        # Measure validation time
        start_time = time.time()
        validator = MockDataValidator(large_data)
        validator.validate_nulls('name')
        end_time = time.time()
        
        # Assert reasonable performance (less than 1 second)
        assert (end_time - start_time) < 1.0
    
    def test_memory_usage(self):
        """Test memory usage with large dataset"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and process large dataset
        large_data = TestDataGenerator.create_clean_dataset(50000)
        validator = MockDataValidator(large_data)
        validator.validate_nulls('name')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert reasonable memory usage (less than 100MB increase)
        assert memory_increase < 100 * 1024 * 1024

# Parameterized tests
class TestParameterizedValidation:
    """Parameterized tests for different validation scenarios"""
    
    @pytest.mark.parametrize("column,expected_nulls", [
        ('name', 0),
        ('age', 0),
        ('email', 0),
        ('salary', 0)
    ])
    def test_null_validation_multiple_columns(self, clean_data, column, expected_nulls):
        """Test null validation across multiple columns"""
        validator = MockDataValidator(clean_data)
        result = validator.validate_nulls(column)
        assert result['null_count'] == expected_nulls
    
    @pytest.mark.parametrize("dataset_size", [10, 100, 1000])
    def test_validation_different_sizes(self, dataset_size):
        """Test validation with different dataset sizes"""
        data = TestDataGenerator.create_clean_dataset(dataset_size)
        validator = MockDataValidator(data)
        result = validator.validate_nulls('name')
        
        assert result['passed'] is True
        assert len(data) == dataset_size

# Mock and patch tests
class TestMockingAndPatching:
    """Tests using mocking and patching"""
    
    @patch('pandas.read_csv')
    def test_file_loading_with_mock(self, mock_read_csv, clean_data):
        """Test file loading with mocked pandas.read_csv"""
        mock_read_csv.return_value = clean_data
        
        # Simulate loading data
        df = pd.read_csv('fake_file.csv')
        
        # Verify mock was called
        mock_read_csv.assert_called_once_with('fake_file.csv')
        
        # Verify data is as expected
        assert len(df) == len(clean_data)
        assert list(df.columns) == list(clean_data.columns)
    
    def test_validation_with_mock_database(self):
        """Test validation with mocked database connection"""
        # Create mock database
        mock_db = Mock()
        mock_db.execute.return_value = [{'count': 100}]
        
        # Simulate database validation
        result = mock_db.execute("SELECT COUNT(*) as count FROM table")
        
        # Verify mock interaction
        mock_db.execute.assert_called_once()
        assert result[0]['count'] == 100

# Test configuration and setup
class TestConfiguration:
    """Tests for configuration and setup"""
    
    def test_test_data_generator_consistency(self):
        """Test that data generator produces consistent results"""
        data1 = TestDataGenerator.create_clean_dataset(100)
        data2 = TestDataGenerator.create_clean_dataset(100)
        
        # Should be identical due to fixed seed
        pd.testing.assert_frame_equal(data1, data2)
    
    def test_fixture_isolation(self, clean_data, dirty_data):
        """Test that fixtures are properly isolated"""
        # Modify clean data
        clean_data.loc[0, 'name'] = 'Modified'
        
        # Dirty data should be unaffected
        assert dirty_data.loc[0, 'name'] != 'Modified'

# Custom test utilities
class TestUtilities:
    """Utility functions for testing"""
    
    @staticmethod
    def assert_data_quality(df: pd.DataFrame, quality_threshold: float = 0.95):
        """Custom assertion for data quality"""
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        quality_score = 1 - (null_cells / total_cells)
        
        assert quality_score >= quality_threshold, f"Data quality {quality_score:.2f} below threshold {quality_threshold}"
    
    @staticmethod
    def assert_column_exists(df: pd.DataFrame, column: str):
        """Custom assertion for column existence"""
        assert column in df.columns, f"Column '{column}' not found in DataFrame"
    
    def test_custom_assertions(self, clean_data):
        """Test custom assertion functions"""
        self.assert_data_quality(clean_data, 0.9)
        self.assert_column_exists(clean_data, 'name')
        
        with pytest.raises(AssertionError):
            self.assert_column_exists(clean_data, 'nonexistent_column')

# Test runner configuration
if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
```

## Additional Test Files

### conftest.py
```python
import pytest
import pandas as pd
import numpy as np

@pytest.fixture(scope="session")
def sample_config():
    """Session-scoped configuration fixture"""
    return {
        'test_data_size': 100,
        'random_seed': 42,
        'quality_threshold': 0.95
    }

@pytest.fixture(autouse=True)
def setup_numpy_seed():
    """Automatically set numpy seed for all tests"""
    np.random.seed(42)

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
```

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Your Task
1. Run the test suite and understand each test type
2. Add tests for edge cases (empty data, single row, all nulls)
3. Create performance benchmarks for different data sizes
4. Implement test data factories for different domains (financial, healthcare, etc.)
5. Add property-based tests using the `hypothesis` library
6. Create integration tests that test the entire data pipeline

## Key Concepts to Master
- Unit testing vs integration testing
- Test fixtures and dependency injection
- Mocking external dependencies
- Property-based testing
- Performance testing and benchmarking
- Test data generation strategies
- Test organization and configuration