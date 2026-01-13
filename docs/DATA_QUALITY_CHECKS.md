# Data Quality Checks Documentation

## Overview
Data quality checks are validations performed on data to ensure it meets business requirements and technical standards before loading into the data warehouse. These checks catch issues early, prevent bad data from propagating, and maintain data integrity.

---

## 1. **Null/Missing Value Checks**
**Purpose:** Ensure required fields contain values and no critical data is missing.

**Why it matters:** Missing values in key columns can break downstream processes, cause incorrect calculations, and lead to incomplete business insights.

**Implementation:** Check each column for NULL values and flag records where required fields are empty.

**Example:** A customer record without an email address cannot be contacted or used for marketing campaigns.

---

## 2. **Duplicate Record Checks**
**Purpose:** Identify and flag duplicate rows based on primary key or unique identifier columns.

**Why it matters:** Duplicates skew metrics, inflate counts, and can cause referential integrity violations in joins.

**Implementation:** Group by primary key columns and count occurrences; flag any count > 1.

**Example:** Two identical customer records with the same customer_id would double-count that customer in reports.

---

## 3. **Data Type Validation**
**Purpose:** Verify that column values match their expected data types.

**Why it matters:** Type mismatches cause casting errors, failed calculations, and incorrect sorting/filtering.

**Implementation:** Attempt to cast values to expected types; catch and log conversion failures.

**Example:** An age column containing "twenty-five" instead of 25 cannot be used in numeric calculations.

---

## 4. **Range/Boundary Checks**
**Purpose:** Ensure numeric and date values fall within acceptable ranges.

**Why it matters:** Out-of-range values often indicate data entry errors or system issues.

**Implementation:** Compare values against min/max thresholds; flag violations.

**Example:** An age of 150 or -5 is biologically impossible and likely a data error.

---

## 5. **Format Validation**
**Purpose:** Verify that string values match expected patterns (regex, length, etc.).

**Why it matters:** Inconsistent formats break parsing, matching, and downstream processing.

**Implementation:** Use regex patterns or string length checks to validate format compliance.

**Example:** Email addresses should match pattern `user@domain.com`; phone numbers should be formatted consistently.

---

## 6. **Referential Integrity Checks**
**Purpose:** Ensure foreign key values exist in their referenced tables.

**Why it matters:** Orphaned records (referencing non-existent parent records) break joins and cause data loss.

**Implementation:** Join child table to parent table and identify unmatched records.

**Example:** An order with a customer_id that doesn't exist in the customers table is orphaned.

---

## 7. **Business Logic Validation**
**Purpose:** Verify data conforms to business rules and domain constraints.

**Why it matters:** Data may be technically valid but violate business requirements.

**Implementation:** Apply domain-specific rules (e.g., order_date ≤ delivery_date).

**Example:** An order cannot be delivered before it was placed.

---

## 8. **Uniqueness Checks**
**Purpose:** Ensure columns that should be unique contain no duplicates.

**Why it matters:** Duplicate unique values violate database constraints and cause conflicts.

**Implementation:** Count distinct values vs. total values; flag if counts differ.

**Example:** Each customer_id should appear only once in the customers table.

---

## 9. **Consistency Checks**
**Purpose:** Verify data consistency across related columns or tables.

**Why it matters:** Inconsistent data leads to incorrect analysis and broken relationships.

**Implementation:** Compare related columns for logical consistency.

**Example:** If a customer's signup_date is in the future, it's inconsistent with the current date.

---

## 10. **Completeness Checks**
**Purpose:** Verify that all expected records are present (no missing batches or files).

**Why it matters:** Missing data leads to incomplete analysis and incorrect metrics.

**Implementation:** Compare record counts against expected totals or previous loads.

**Example:** If yesterday's load had 1000 customers and today's has 500, investigate why.

---

## 11. **Outlier Detection**
**Purpose:** Identify unusual or anomalous values that deviate from normal patterns.

**Why it matters:** Outliers may indicate data quality issues or require special handling.

**Implementation:** Use statistical methods (z-score, IQR) to flag extreme values.

**Example:** A customer with 10,000 orders when the average is 5 may be a data error or a VIP.

---

## 12. **Whitespace and Case Consistency**
**Purpose:** Ensure text fields don't have leading/trailing whitespace and follow consistent casing.

**Why it matters:** Whitespace and case differences prevent proper matching and deduplication.

**Implementation:** Check for leading/trailing spaces; flag inconsistent casing.

**Example:** "John Smith" vs " John Smith " should be treated as the same value.

---

## Summary Table

| Check | Input | Output | Action |
|-------|-------|--------|--------|
| Null Check | Column data | Count of NULLs | Flag/Reject if critical field is NULL |
| Duplicates | Primary key | Duplicate count | Flag/Reject if duplicates found |
| Data Type | Column values | Type mismatch count | Flag/Reject if type conversion fails |
| Range | Numeric/Date values | Out-of-range count | Flag/Reject if outside bounds |
| Format | String values | Format mismatch count | Flag/Reject if pattern doesn't match |
| Referential | Foreign keys | Orphaned record count | Flag/Reject if FK doesn't exist |
| Business Logic | Related columns | Rule violation count | Flag/Reject if rule violated |
| Uniqueness | Unique columns | Duplicate count | Flag/Reject if duplicates found |
| Consistency | Related columns | Inconsistency count | Flag/Reject if inconsistent |
| Completeness | Record count | Count vs. expected | Flag/Reject if count mismatch |
| Outliers | Numeric values | Outlier count | Flag for review |
| Whitespace/Case | String values | Issue count | Flag/Reject if issues found |
