# Project 1: Data Cleaning Pipeline

## Overview
Build a basic ETL pipeline that cleans messy data and validates the results.

## Skills You'll Learn
- Pandas operations
- Basic data validation
- Function composition
- Error handling

## Implementation

```python
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class DataCleaner:
    """Basic data cleaning pipeline"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.cleaning_log = []
    
    def remove_duplicates(self, subset: Optional[List[str]] = None) -> 'DataCleaner':
        """Remove duplicate rows"""
        before_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset)
        after_count = len(self.df)
        
        self.cleaning_log.append(f"Removed {before_count - after_count} duplicates")
        return self
    
    def fill_missing_values(self, strategy: Dict[str, str]) -> 'DataCleaner':
        """Fill missing values with different strategies per column"""
        for column, method in strategy.items():
            if column not in self.df.columns:
                continue
            
            missing_count = self.df[column].isnull().sum()
            
            if method == 'mean':
                self.df[column].fillna(self.df[column].mean(), inplace=True)
            elif method == 'median':
                self.df[column].fillna(self.df[column].median(), inplace=True)
            elif method == 'mode':
                self.df[column].fillna(self.df[column].mode()[0], inplace=True)
            elif method == 'forward':
                self.df[column].fillna(method='ffill', inplace=True)
            elif isinstance(method, (str, int, float)):
                self.df[column].fillna(method, inplace=True)
            
            self.cleaning_log.append(f"Filled {missing_count} missing values in {column}")
        
        return self
    
    def standardize_text(self, columns: List[str]) -> 'DataCleaner':
        """Standardize text columns (strip, lower, etc.)"""
        for column in columns:
            if column in self.df.columns:
                self.df[column] = self.df[column].astype(str).str.strip().str.lower()
                self.cleaning_log.append(f"Standardized text in {column}")
        
        return self
    
    def remove_outliers(self, column: str, method: str = 'iqr') -> 'DataCleaner':
        """Remove statistical outliers"""
        if column not in self.df.columns:
            return self
        
        before_count = len(self.df)
        
        if method == 'iqr':
            Q1 = self.df[column].quantile(0.25)
            Q3 = self.df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            self.df = self.df[(self.df[column] >= lower_bound) & (self.df[column] <= upper_bound)]
        
        after_count = len(self.df)
        self.cleaning_log.append(f"Removed {before_count - after_count} outliers from {column}")
        
        return self
    
    def validate_data_types(self, type_mapping: Dict[str, str]) -> Dict[str, bool]:
        """Validate that columns can be converted to expected types"""
        validation_results = {}
        
        for column, expected_type in type_mapping.items():
            if column not in self.df.columns:
                validation_results[column] = False
                continue
            
            try:
                if expected_type == 'int':
                    pd.to_numeric(self.df[column], errors='raise')
                elif expected_type == 'float':
                    pd.to_numeric(self.df[column], errors='raise')
                elif expected_type == 'datetime':
                    pd.to_datetime(self.df[column], errors='raise')
                
                validation_results[column] = True
            except:
                validation_results[column] = False
        
        return validation_results
    
    def get_cleaned_data(self) -> pd.DataFrame:
        """Return the cleaned DataFrame"""
        return self.df
    
    def get_cleaning_report(self) -> List[str]:
        """Return log of all cleaning operations"""
        return self.cleaning_log

# Example usage
def create_messy_data():
    """Generate messy sample data"""
    data = {
        'name': ['John Doe', '  jane smith  ', 'MIKE JONES', 'John Doe', None],
        'age': [25, 30, None, 25, 150],
        'email': ['john@email.com', 'jane@email.com', 'mike@email.com', 'john@email.com', 'invalid-email'],
        'salary': [50000, 60000, 70000, 50000, None]
    }
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Create and clean messy data
    messy_df = create_messy_data()
    print("Original data:")
    print(messy_df)
    
    # Clean the data
    cleaner = DataCleaner(messy_df)
    cleaned_df = (cleaner
                  .remove_duplicates()
                  .fill_missing_values({'age': 'median', 'salary': 'mean'})
                  .standardize_text(['name'])
                  .remove_outliers('age')
                  .get_cleaned_data())
    
    print("\nCleaned data:")
    print(cleaned_df)
    
    print("\nCleaning report:")
    for step in cleaner.get_cleaning_report():
        print(f"- {step}")
    
    # Validate data types
    type_validation = cleaner.validate_data_types({
        'age': 'int',
        'salary': 'float'
    })
    print(f"\nType validation: {type_validation}")
```

## Your Task
1. Run this code and understand each method
2. Add a method to validate email formats using regex
3. Add a method to handle date parsing and validation
4. Create your own messy dataset and clean it
5. Add logging to track what percentage of data was cleaned

## Key Concepts to Master
- Method chaining (fluent interface)
- Data type validation
- Statistical outlier detection
- Text standardization
- Missing value strategies