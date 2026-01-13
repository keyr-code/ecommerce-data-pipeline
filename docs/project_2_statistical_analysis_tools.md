# Project 2: Statistical Analysis Tools

## Overview
Build a data profiling utility that generates comprehensive statistical summaries.

## Skills You'll Learn
- Statistical analysis with pandas/numpy
- Data visualization concepts
- Summary statistics
- Distribution analysis

## Implementation

```python
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from scipy import stats

@dataclass
class ColumnProfile:
    """Statistical profile for a single column"""
    name: str
    dtype: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    
    # Numeric stats (if applicable)
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    
    # Text stats (if applicable)
    avg_length: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    # Top values
    top_values: Optional[Dict[Any, int]] = None

class DataProfiler:
    """Comprehensive data profiling tool"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.profiles: Dict[str, ColumnProfile] = {}
    
    def profile_column(self, column: str) -> ColumnProfile:
        """Generate detailed profile for a single column"""
        series = self.df[column]
        
        # Basic stats
        profile = ColumnProfile(
            name=column,
            dtype=str(series.dtype),
            count=len(series),
            null_count=series.isnull().sum(),
            null_percentage=(series.isnull().sum() / len(series)) * 100,
            unique_count=series.nunique(),
            unique_percentage=(series.nunique() / len(series)) * 100,
            top_values=series.value_counts().head(5).to_dict()
        )
        
        # Numeric statistics
        if pd.api.types.is_numeric_dtype(series):
            numeric_series = series.dropna()
            if len(numeric_series) > 0:
                profile.mean = numeric_series.mean()
                profile.median = numeric_series.median()
                profile.std = numeric_series.std()
                profile.min_val = numeric_series.min()
                profile.max_val = numeric_series.max()
                profile.q25 = numeric_series.quantile(0.25)
                profile.q75 = numeric_series.quantile(0.75)
        
        # Text statistics
        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            text_series = series.dropna().astype(str)
            if len(text_series) > 0:
                lengths = text_series.str.len()
                profile.avg_length = lengths.mean()
                profile.min_length = lengths.min()
                profile.max_length = lengths.max()
        
        return profile
    
    def profile_all_columns(self) -> Dict[str, ColumnProfile]:
        """Profile all columns in the DataFrame"""
        for column in self.df.columns:
            self.profiles[column] = self.profile_column(column)
        return self.profiles
    
    def detect_data_quality_issues(self) -> Dict[str, List[str]]:
        """Detect potential data quality issues"""
        issues = {}
        
        for column, profile in self.profiles.items():
            column_issues = []
            
            # High null percentage
            if profile.null_percentage > 50:
                column_issues.append(f"High null rate: {profile.null_percentage:.1f}%")
            
            # Low cardinality (might be categorical)
            if profile.unique_percentage < 5 and profile.unique_count > 1:
                column_issues.append(f"Low cardinality: {profile.unique_count} unique values")
            
            # Potential outliers in numeric columns
            if profile.mean is not None and profile.std is not None:
                if profile.std > profile.mean * 2:  # High variance
                    column_issues.append("High variance detected - potential outliers")
            
            # Very long text fields
            if profile.max_length is not None and profile.max_length > 1000:
                column_issues.append(f"Very long text detected: max {profile.max_length} characters")
            
            if column_issues:
                issues[column] = column_issues
        
        return issues
    
    def generate_summary_report(self) -> str:
        """Generate a text summary report"""
        if not self.profiles:
            self.profile_all_columns()
        
        report = []
        report.append("DATA PROFILING REPORT")
        report.append("=" * 50)
        report.append(f"Dataset shape: {self.df.shape}")
        report.append(f"Total columns: {len(self.df.columns)}")
        report.append(f"Total rows: {len(self.df)}")
        report.append("")
        
        # Column summaries
        for column, profile in self.profiles.items():
            report.append(f"Column: {column}")
            report.append(f"  Type: {profile.dtype}")
            report.append(f"  Nulls: {profile.null_count} ({profile.null_percentage:.1f}%)")
            report.append(f"  Unique: {profile.unique_count} ({profile.unique_percentage:.1f}%)")
            
            if profile.mean is not None:
                report.append(f"  Mean: {profile.mean:.2f}")
                report.append(f"  Median: {profile.median:.2f}")
                report.append(f"  Range: {profile.min_val:.2f} - {profile.max_val:.2f}")
            
            if profile.avg_length is not None:
                report.append(f"  Avg length: {profile.avg_length:.1f}")
                report.append(f"  Length range: {profile.min_length} - {profile.max_length}")
            
            report.append(f"  Top values: {list(profile.top_values.keys())[:3]}")
            report.append("")
        
        # Data quality issues
        issues = self.detect_data_quality_issues()
        if issues:
            report.append("DATA QUALITY ISSUES")
            report.append("-" * 30)
            for column, column_issues in issues.items():
                report.append(f"{column}:")
                for issue in column_issues:
                    report.append(f"  - {issue}")
            report.append("")
        
        return "\n".join(report)
    
    def compare_distributions(self, column1: str, column2: str) -> Dict[str, Any]:
        """Compare distributions between two numeric columns"""
        if column1 not in self.df.columns or column2 not in self.df.columns:
            return {"error": "One or both columns not found"}
        
        series1 = pd.to_numeric(self.df[column1], errors='coerce').dropna()
        series2 = pd.to_numeric(self.df[column2], errors='coerce').dropna()
        
        if len(series1) == 0 or len(series2) == 0:
            return {"error": "No numeric data found"}
        
        # Statistical comparison
        correlation = series1.corr(series2) if len(series1) == len(series2) else None
        
        # Distribution comparison using Kolmogorov-Smirnov test
        try:
            ks_statistic, ks_p_value = stats.ks_2samp(series1, series2)
        except:
            ks_statistic, ks_p_value = None, None
        
        return {
            "correlation": correlation,
            "ks_statistic": ks_statistic,
            "ks_p_value": ks_p_value,
            "same_distribution": ks_p_value > 0.05 if ks_p_value else None,
            "summary_stats": {
                column1: {"mean": series1.mean(), "std": series1.std()},
                column2: {"mean": series2.mean(), "std": series2.std()}
            }
        }
    
    def detect_anomalies(self, column: str, method: str = 'iqr') -> pd.Series:
        """Detect anomalies in a numeric column"""
        if column not in self.df.columns:
            return pd.Series(dtype=bool)
        
        series = pd.to_numeric(self.df[column], errors='coerce')
        
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (series < lower_bound) | (series > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(series.dropna()))
            # Map back to original series length
            anomalies = pd.Series(False, index=series.index)
            anomalies.loc[series.dropna().index] = z_scores > 3
            return anomalies
        
        return pd.Series(False, index=series.index)

# Example usage
def create_sample_data():
    """Create sample data for profiling"""
    np.random.seed(42)
    
    data = {
        'customer_id': range(1, 1001),
        'age': np.random.normal(35, 12, 1000).astype(int),
        'income': np.random.lognormal(10, 0.5, 1000),
        'city': np.random.choice(['NYC', 'LA', 'Chicago', 'Houston'], 1000),
        'signup_date': pd.date_range('2020-01-01', periods=1000, freq='D'),
        'email_domain': np.random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'], 1000)
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some data quality issues
    df.loc[np.random.choice(1000, 50, replace=False), 'age'] = None
    df.loc[np.random.choice(1000, 20, replace=False), 'income'] = df['income'].max() * 10  # Outliers
    
    return df

if __name__ == "__main__":
    # Create and profile sample data
    df = create_sample_data()
    profiler = DataProfiler(df)
    
    # Generate profiles
    profiles = profiler.profile_all_columns()
    
    # Print summary report
    print(profiler.generate_summary_report())
    
    # Compare distributions
    comparison = profiler.compare_distributions('age', 'income')
    print("Age vs Income comparison:")
    print(f"Correlation: {comparison.get('correlation', 'N/A')}")
    
    # Detect anomalies
    income_anomalies = profiler.detect_anomalies('income', method='iqr')
    print(f"\nIncome anomalies detected: {income_anomalies.sum()}")
```

## Your Task
1. Run this code and understand the statistical concepts
2. Add methods to detect seasonal patterns in time series data
3. Implement categorical data analysis (mode, frequency analysis)
4. Add correlation matrix generation for all numeric columns
5. Create a method to suggest data types based on content analysis

## Key Concepts to Master
- Descriptive statistics (mean, median, quartiles)
- Distribution analysis and comparison
- Outlier detection methods (IQR, Z-score)
- Correlation analysis
- Data type inference
- Statistical testing (Kolmogorov-Smirnov)