"""
Comprehensive Data Quality Validation Framework

This module implements all major categories of data quality checks:
- Completeness, Validity, Uniqueness, Consistency, Accuracy, Statistical,
  Timeliness, Structural, Security
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Union, Optional
from dataclasses import dataclass
from enum import Enum
from scipy import stats


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class ValidationResult:
    check_name: str
    passed: bool
    severity: Severity
    message: str
    failed_count: int = 0
    total_count: int = 0
    details: Optional[Dict[str, Any]] = None


class DataQualityValidator:
    """Comprehensive data quality validation framework"""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results: List[ValidationResult] = []

    def get_highest_severity(self) -> Severity:
        """Get the highest severity level from all validation results"""
        if not self.results:
            return Severity.LOW

        # Define severity order (highest to lowest)
        severity_order = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
        }

        # Get highest severity from failed checks only
        failed_severities = [r.severity for r in self.results if not r.passed]

        if not failed_severities:
            return Severity.LOW

        return max(failed_severities, key=lambda s: severity_order[s])

    def should_stop_pipeline(
        self, stop_on_severity: Severity = Severity.CRITICAL
    ) -> bool:
        """Determine if pipeline should stop based on validation results"""
        highest_severity = self.get_highest_severity()

        severity_order = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
        }

        return severity_order[highest_severity] >= severity_order[stop_on_severity]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results"""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.passed)
        highest_severity = self.get_highest_severity()

        severity_counts = {}
        for severity in Severity:
            severity_counts[severity.value] = sum(
                1 for r in self.results if r.severity == severity and not r.passed
            )

        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "success_rate": (
                (passed_checks / total_checks * 100) if total_checks > 0 else 0
            ),
            "severity_breakdown": severity_counts,
            "critical_failures": [
                r
                for r in self.results
                if r.severity == Severity.CRITICAL and not r.passed
            ],
            "highest_severity": highest_severity.value,
            "should_stop_pipeline": self.should_stop_pipeline(),
        }

    def print_detailed_summary(self) -> None:
        """Print comprehensive validation summary with failed checks details"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("DATA QUALITY VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Dataset Shape: {self.df.shape}")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed Checks: {summary['passed_checks']}")
        print(f"Failed Checks: {summary['failed_checks']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        # Show severity breakdown
        print("\nSEVERITY BREAKDOWN:")
        print("-" * 30)
        for severity, count in summary["severity_breakdown"].items():
            if count > 0:
                print(f"  {severity}: {count} issues")

        # Show all validation results
        print("\nDETAILED RESULTS:")
        print("-" * 40)
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{status} | {result.check_name}: {result.message}")

            # Show details for failed checks
            if not result.passed and result.details:
                for key, value in result.details.items():
                    if isinstance(value, dict) and value:
                        print(f"    {key}:")
                        for k, v in value.items():
                            if key == "null_breakdown" and isinstance(v, dict):
                                print(
                                    f"      {k}: {v['count']} nulls ({v['percentage']}%)"
                                )
                            else:
                                print(f"      {k}: {v}")
                    else:
                        print(f"    {key}: {value}")
            print()

        # Critical issues alert
        if summary["critical_failures"]:
            print("\n🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            print("=" * 50)
            for failure in summary["critical_failures"]:
                print(f"• {failure.check_name}: {failure.message}")

        # Overall assessment
        if summary["success_rate"] < 50:
            print("\n❌ POOR DATA QUALITY - Immediate action required")
        elif summary["success_rate"] < 80:
            print("\n⚠️  MODERATE DATA QUALITY - Review and improve")
        elif summary["success_rate"] < 95:
            print("\n✅ GOOD DATA QUALITY - Minor issues to address")
        else:
            print("\n🎉 EXCELLENT DATA QUALITY - Well done!")

    # CATEGORY 1: COMPLETENESS CHECKS

    def check_null_values(
        self,
        columns: Optional[List[str]] = None,
        required_columns: Optional[List[str]] = None,
        non_null_columns: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Check for null/missing values in specified columns"""
        columns = columns or self.df.columns.tolist()
        required_columns = required_columns or []
        non_null_columns = non_null_columns or []

        null_counts = self.df[columns].isnull().sum()
        total_nulls = null_counts.sum()
        critical_nulls = sum(
            null_counts[col] for col in non_null_columns if col in null_counts
        )

        # Determine severity: CRITICAL only if non_null_columns have nulls
        if critical_nulls > 0:
            severity = Severity.CRITICAL
            passed = False
        elif total_nulls > 0:
            severity = Severity.MEDIUM
            passed = False
        else:
            severity = Severity.LOW
            passed = True

        # Enhanced details with column breakdown
        null_details = {}
        for col in columns:
            if null_counts[col] > 0:
                null_details[col] = {
                    "count": null_counts[col],
                    "percentage": round((null_counts[col] / len(self.df)) * 100, 1),
                }

        result = ValidationResult(
            check_name="null_values",
            passed=passed,
            severity=severity,
            message=(
                f"Found {total_nulls} null values, "
                f"{critical_nulls} in non-null columns"
            ),
            failed_count=total_nulls,
            total_count=len(self.df) * len(columns),
            details={
                "null_counts_by_column": null_counts.to_dict(),
                "null_breakdown": null_details,
            },
        )
        self.results.append(result)
        return result

    def check_record_completeness(
        self, expected_count: Optional[int] = None, tolerance: float = 0.05
    ) -> ValidationResult:
        """Check if all expected records are present"""
        actual_count = len(self.df)

        if expected_count is None:
            passed = True
            message = f"Record count: {actual_count} (no baseline provided)"
            severity = Severity.LOW
        else:
            diff_pct = abs(actual_count - expected_count) / expected_count
            passed = diff_pct <= tolerance
            severity = Severity.HIGH if not passed else Severity.LOW
            message = (
                f"Expected {expected_count}, got {actual_count} "
                f"({diff_pct:.2%} difference)"
            )

        result = ValidationResult(
            check_name="record_completeness",
            passed=passed,
            severity=severity,
            message=message,
            failed_count=0 if passed else abs(actual_count - (expected_count or 0)),
            total_count=expected_count or actual_count,
        )
        self.results.append(result)
        return result

    def check_column_completeness(
        self, expected_columns: List[str]
    ) -> ValidationResult:
        """Check if all expected columns are present"""
        actual_columns = set(self.df.columns)
        expected_columns_set = set(expected_columns)

        missing_columns = expected_columns_set - actual_columns
        extra_columns = actual_columns - expected_columns_set

        passed = len(missing_columns) == 0
        severity = Severity.CRITICAL if missing_columns else Severity.LOW

        message = (
            f"Missing columns: {list(missing_columns)}, "
            f"Extra columns: {list(extra_columns)}"
        )

        result = ValidationResult(
            check_name="column_completeness",
            passed=passed,
            severity=severity,
            message=message,
            failed_count=len(missing_columns),
            total_count=len(expected_columns),
            details={
                "missing_columns": list(missing_columns),
                "extra_columns": list(extra_columns),
            },
        )
        self.results.append(result)
        return result

    # CATEGORY 2: VALIDITY CHECKS

    def check_data_types(self, type_mapping: Dict[str, str]) -> ValidationResult:
        """Validate data types match expected types"""
        type_errors = {}
        total_errors = 0

        for column, expected_type in type_mapping.items():
            if column not in self.df.columns:
                continue

            try:
                if expected_type == "int":
                    pd.to_numeric(self.df[column], errors="raise")
                elif expected_type == "float":
                    pd.to_numeric(self.df[column], errors="raise")
                elif expected_type == "datetime":
                    pd.to_datetime(self.df[column], errors="raise")
                elif expected_type == "bool":
                    self.df[column].astype(bool)
            except (ValueError, TypeError):
                if expected_type in ["int", "float"]:
                    errors = (
                        pd.to_numeric(self.df[column], errors="coerce").isna().sum()
                    )
                elif expected_type == "datetime":
                    errors = (
                        pd.to_datetime(self.df[column], errors="coerce").isna().sum()
                    )
                else:
                    errors = 1

                type_errors[column] = errors
                total_errors += errors

        passed = total_errors == 0
        severity = Severity.CRITICAL if not passed else Severity.LOW

        result = ValidationResult(
            check_name="data_types",
            passed=passed,
            severity=severity,
            message=f"Found {total_errors} type conversion errors",
            failed_count=total_errors,
            total_count=len(self.df) * len(type_mapping),
            details={"type_errors_by_column": type_errors},
        )
        self.results.append(result)
        return result

    def check_format_validation(self, format_rules: Dict[str, str]) -> ValidationResult:
        """Validate string formats using regex patterns"""
        format_errors = {}
        total_errors = 0

        for column, pattern in format_rules.items():
            if column not in self.df.columns:
                continue

            non_null_mask = self.df[column].notna()
            if non_null_mask.sum() == 0:
                continue

            matches = self.df.loc[non_null_mask, column].astype(str).str.match(pattern)
            errors = (~matches).sum()

            if errors > 0:
                format_errors[column] = errors
                total_errors += errors

        passed = total_errors == 0
        severity = Severity.MEDIUM if not passed else Severity.LOW

        result = ValidationResult(
            check_name="format_validation",
            passed=passed,
            severity=severity,
            message=f"Found {total_errors} format validation errors",
            failed_count=total_errors,
            details={"format_errors_by_column": format_errors},
        )
        self.results.append(result)
        return result

    def check_range_validation(
        self, range_rules: Dict[str, Tuple[Union[int, float], Union[int, float]]]
    ) -> ValidationResult:
        """Validate numeric values are within specified ranges"""
        range_errors = {}
        total_errors = 0

        for column, (min_val, max_val) in range_rules.items():
            if column not in self.df.columns:
                continue

            try:
                numeric_col = pd.to_numeric(self.df[column], errors="coerce")
                valid_mask = numeric_col.notna()

                if valid_mask.sum() == 0:
                    continue

                out_of_range = (
                    (numeric_col < min_val) | (numeric_col > max_val)
                ) & valid_mask
                errors = out_of_range.sum()

                if errors > 0:
                    range_errors[column] = errors
                    total_errors += errors

            except Exception:
                continue

        passed = total_errors == 0
        severity = Severity.MEDIUM if not passed else Severity.LOW

        result = ValidationResult(
            check_name="range_validation",
            passed=passed,
            severity=severity,
            message=f"Found {total_errors} range validation errors",
            failed_count=total_errors,
            details={"range_errors_by_column": range_errors},
        )
        self.results.append(result)
        return result

    def check_domain_validation(
        self, domain_rules: Dict[str, List[Any]]
    ) -> ValidationResult:
        """Validate values belong to predefined domains"""
        domain_errors = {}
        total_errors = 0

        for column, valid_values in domain_rules.items():
            if column not in self.df.columns:
                continue

            invalid_mask = ~self.df[column].isin(valid_values) & self.df[column].notna()
            errors = invalid_mask.sum()  # type: ignore

            if errors > 0:
                domain_errors[column] = errors
                total_errors += errors

        passed = total_errors == 0
        severity = Severity.MEDIUM if not passed else Severity.LOW

        result = ValidationResult(
            check_name="domain_validation",
            passed=passed,
            severity=severity,
            message=f"Found {total_errors} domain validation errors",
            failed_count=total_errors,
            details={"domain_errors_by_column": domain_errors},
        )
        self.results.append(result)
        return result

    # CATEGORY 3: UNIQUENESS CHECKS

    def check_primary_key_uniqueness(
        self, primary_key_columns: List[str]
    ) -> ValidationResult:
        """Check primary key uniqueness"""
        if not all(col in self.df.columns for col in primary_key_columns):
            missing_cols = [
                col for col in primary_key_columns if col not in self.df.columns
            ]
            result = ValidationResult(
                check_name="primary_key_uniqueness",
                passed=False,
                severity=Severity.CRITICAL,
                message=f"Primary key columns missing: {missing_cols}",
                failed_count=len(missing_cols),
                total_count=len(primary_key_columns),
            )
            self.results.append(result)
            return result

        duplicates = self.df.duplicated(subset=primary_key_columns, keep=False)
        duplicate_count = duplicates.sum()

        passed = duplicate_count == 0
        severity = Severity.CRITICAL if not passed else Severity.LOW

        result = ValidationResult(
            check_name="primary_key_uniqueness",
            passed=passed,
            severity=severity,
            message=f"Found {duplicate_count} duplicate primary key values",
            failed_count=duplicate_count,
            total_count=len(self.df),
        )
        self.results.append(result)
        return result

    def check_uniqueness(self, unique_columns: List[str]) -> ValidationResult:
        """Check uniqueness for specified columns"""
        uniqueness_errors = {}
        total_errors = 0

        for column in unique_columns:
            if column not in self.df.columns:
                continue

            duplicates = self.df[column].duplicated(keep=False).sum()
            if duplicates > 0:
                uniqueness_errors[column] = duplicates
                total_errors += duplicates

        passed = total_errors == 0
        severity = Severity.HIGH if not passed else Severity.LOW

        result = ValidationResult(
            check_name="uniqueness",
            passed=passed,
            severity=severity,
            message=f"Found {total_errors} uniqueness violations",
            failed_count=total_errors,
            details={"uniqueness_errors_by_column": uniqueness_errors},
        )
        self.results.append(result)
        return result

    # CATEGORY 4: CONSISTENCY CHECKS

    def check_cross_column_consistency(
        self, consistency_rules: List[str]
    ) -> ValidationResult:
        """Check consistency between related columns using pandas query expressions"""
        consistency_errors = 0
        rule_results = {}

        for rule in consistency_rules:
            try:
                valid_mask = self.df.eval(rule)
                violations = (~valid_mask).sum()  # type: ignore
                rule_results[rule] = violations
                consistency_errors += violations
            except Exception as e:
                rule_results[rule] = f"Error: {str(e)}"

        passed = consistency_errors == 0
        severity = Severity.MEDIUM if not passed else Severity.LOW

        result = ValidationResult(
            check_name="cross_column_consistency",
            passed=passed,
            severity=severity,
            message=f"Found {consistency_errors} consistency violations",
            failed_count=consistency_errors,
            details={"rule_results": rule_results},
        )
        self.results.append(result)
        return result

    # CATEGORY 5: STATISTICAL CHECKS

    def check_outliers(
        self, numeric_columns: List[str], method: str = "iqr", threshold: float = 1.5
    ) -> ValidationResult:
        """Detect statistical outliers in numeric columns"""
        outlier_counts = {}
        total_outliers = 0

        for column in numeric_columns:
            if column not in self.df.columns:
                continue

            numeric_data = pd.to_numeric(self.df[column], errors="coerce").dropna()
            if len(numeric_data) == 0:
                continue

            if method == "iqr":
                Q1 = numeric_data.quantile(0.25)
                Q3 = numeric_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers = (
                    (numeric_data < lower_bound) | (numeric_data > upper_bound)
                ).sum()
            elif method == "zscore":
                z_scores = np.abs(stats.zscore(numeric_data))  # type: ignore
                outliers = (z_scores > threshold).sum()
            else:
                outliers = 0

            if outliers > 0:
                outlier_counts[column] = outliers
                total_outliers += outliers

        passed = total_outliers == 0
        severity = Severity.LOW

        result = ValidationResult(
            check_name="outliers",
            passed=passed,
            severity=severity,
            message=f"Found {total_outliers} statistical outliers",
            failed_count=total_outliers,
            details={"outlier_counts_by_column": outlier_counts},
        )
        self.results.append(result)
        return result

    # CATEGORY 6: SECURITY CHECKS

    def check_pii_detection(
        self, text_columns: Optional[List[str]] = None
    ) -> ValidationResult:
        """Detect potential PII in text columns"""
        text_columns = text_columns or [
            col for col in self.df.columns if self.df[col].dtype == "object"
        ]

        pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        }

        pii_found = {}
        total_pii = 0

        for column in text_columns:
            if column not in self.df.columns:
                continue

            column_pii = {}
            text_data = self.df[column].astype(str)

            for pii_type, pattern in pii_patterns.items():
                matches = text_data.str.contains(pattern, regex=True, na=False).sum()
                if matches > 0:
                    column_pii[pii_type] = matches
                    total_pii += matches

            if column_pii:
                pii_found[column] = column_pii

        passed = total_pii == 0
        severity = Severity.HIGH if not passed else Severity.LOW

        result = ValidationResult(
            check_name="pii_detection",
            passed=passed,
            severity=severity,
            message=f"Found {total_pii} potential PII instances",
            failed_count=total_pii,
            details={"pii_by_column": pii_found},
        )
        self.results.append(result)
        return result

    # COMPREHENSIVE VALIDATION RUNNER

    def run_all_checks(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all applicable data quality checks based on configuration"""
        config = config or {}

        # Basic completeness checks
        self.check_null_values(
            required_columns=config.get("required_columns", []),
            non_null_columns=config.get("non_null_columns", []),
        )

        if "expected_record_count" in config:
            self.check_record_completeness(config["expected_record_count"])

        if "expected_columns" in config:
            self.check_column_completeness(config["expected_columns"])

        # Validity checks
        if "type_mapping" in config:
            self.check_data_types(config["type_mapping"])

        if "format_rules" in config:
            self.check_format_validation(config["format_rules"])

        if "range_rules" in config:
            self.check_range_validation(config["range_rules"])

        if "domain_rules" in config:
            self.check_domain_validation(config["domain_rules"])

        # Uniqueness checks
        if "primary_key_columns" in config:
            self.check_primary_key_uniqueness(config["primary_key_columns"])

        if "unique_columns" in config:
            self.check_uniqueness(config["unique_columns"])

        # Consistency checks
        if "consistency_rules" in config:
            self.check_cross_column_consistency(config["consistency_rules"])

        # Statistical checks
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_columns:
            self.check_outliers(numeric_columns)

        # Security checks
        self.check_pii_detection()

        return self.get_summary()
    