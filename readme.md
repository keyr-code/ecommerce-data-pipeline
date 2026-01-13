# E-commerce Data Engineering Pipeline

A medallion architecture data pipeline for e-commerce analytics with Bronze → Silver → Gold layers.

## Architecture Overview

```
Bronze Layer (Raw)     → Silver Layer (Cleaned)    → Gold Layer (Business)
├── raw_customers      ├── customers               ├── fact_sales
├── raw_orders         ├── orders                  ├── dim_customer
├── raw_order_items    ├── order_items             ├── dim_product
├── raw_products       ├── products                ├── customer_metrics
└── raw_employees      └── sales                   ├── top_customers
                                                   ├── revenue_by_category
                                                   └── top_sales_person
```

## Proposed Folder Structure

```
ecommerce/
├── config/                 # Configuration files
│   ├── database.yaml      # Database connections
│   ├── pipeline.yaml      # Pipeline settings
│   └── validation_rules.yaml # Data validation rules
├── data/                   # Data storage
│   ├── bronze/            # Raw data (varchar/string only)
│   ├── silver/            # Cleaned & validated data
│   └── gold/              # Business aggregations
├── src/                    # Source code
│   ├── bronze/            # Raw data ingestion
│   │   ├── data_generator.py # Generate ecommerce data with failures
│   │   └── ingestion.py   # Load raw data
│   ├── silver/            # Data cleaning & validation
│   │   ├── validation.py  # Data validation logic
│   │   ├── cleaning.py    # Data cleaning processes
│   │   └── customer_service_alerts.py # Alert system
│   ├── gold/              # Business metrics
│   │   ├── metrics.py     # Calculate KPIs
│   │   └── aggregations.py # Business aggregations
│   ├── common/            # Shared utilities
│   │   ├── database.py    # Database connections
│   │   └── logger.py      # Logging utilities
│   └── notifications/     # Alert systems
│       └── alerts.py      # Notification handlers
├── sql/                    # SQL scripts
│   ├── bronze/            # Raw table DDL
│   ├── silver/            # Cleaned table DDL
│   └── gold/              # Business table DDL
├── tests/                  # Test suites
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── data_quality/      # Data quality tests
├── docs/                   # Documentation
├── logs/                   # Application logs
└── requirements.txt        # Python dependencies
```

## Data Flow

### Bronze Layer
- **Purpose**: Store raw data as-is with all data types as varchar/string
- **Tables**: raw_customers, raw_orders, raw_order_items, raw_products, raw_employees
- **Process**: Generate ecommerce data with random failures and load directly

### Silver Layer
- **Purpose**: Clean and validate data, handle failures
- **Tables**: customers, orders, order_items, products, sales
- **Process**: 
  - Run validation checks
  - Clean data failures → send alerts to customer service
  - Track incomplete data for relevant entities
  - Send missing sales data alerts to sales manager

### Gold Layer
- **Purpose**: Business-level aggregations and metrics
- **Tables**: fact_sales, dim_customer, dim_product, customer_metrics, top_customers, revenue_by_category, top_sales_person
- **Users**: Data Analysts, Data Scientists, BI Developers

## Key Features

- **Data Generation**: Realistic ecommerce data with intentional failures
- **Validation Framework**: Comprehensive data quality checks
- **Alert System**: Automated notifications for data issues
- **Employee Analytics**: Performance tracking and retention analysis
- **Customer Insights**: Top customers and behavior analysis
- **Sales Metrics**: Revenue tracking and sales person performance

