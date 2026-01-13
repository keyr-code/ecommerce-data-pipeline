# Data Quality Validation Configurations for all CSV files

# Raw Customers Configuration
raw_customer_config = {
    "non_null_columns": ["customer_id", "email"],
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
        "age": "int", 
        "signup_date": "datetime"
    },
    "format_rules": {"email": r".*@.*"},
    "range_rules": {"customer_id": (1, 999999), "age": (0, 120)},
    "primary_key_columns": ["customer_id"],
    "unique_columns": ["email"],
    "consistency_rules": ["customer_id > 0", "age >= 0"],
}

# Products Configuration
products_config = {
    "non_null_columns": ["product_id", "name", "category", "price"],
    "expected_columns": [
        "product_id",
        "name",
        "category",
        "price",
        "stock",
        "supplier_id",
    ],
    "type_mapping": {
        "product_id": "int",
        "price": "float",
        "stock": "int",
        "supplier_id": "int",
    },
    "range_rules": {
        "product_id": (1, 999999),
        "price": (0, 10000),
        "stock": (0, 1000),
        "supplier_id": (1, 100),
    },
    "domain_rules": {
        "category": ["Electronics", "Furniture", "Clothing", "Books", "Home & Garden"]
    },
    "primary_key_columns": ["product_id"],
    "consistency_rules": [
        "product_id > 0",
        "price > 0",
        "stock >= 0",
        "supplier_id > 0",
    ],
}

# Orders Configuration
orders_config = {
    "non_null_columns": [
        "order_id",
        "customer_id",
        "order_date",
        "total_amount",
        "status",
    ],
    "expected_columns": [
        "order_id",
        "customer_id",
        "order_date",
        "total_amount",
        "status",
    ],
    "type_mapping": {
        "order_id": "int",
        "customer_id": "int",
        "order_date": "datetime",
        "total_amount": "float",
    },
    "range_rules": {
        "order_id": (1000, 999999),
        "customer_id": (1, 999999),
        "total_amount": (0, 100000),
    },
    "domain_rules": {"status": ["pending", "completed", "cancelled", "shipped"]},
    "primary_key_columns": ["order_id"],
    "consistency_rules": ["order_id > 0", "customer_id > 0", "total_amount > 0"],
}

# Customers Configuration (processed/clean customers)
customers_config = {
    "non_null_columns": ["customer_id", "email", "name"],
    "expected_columns": [
        "customer_id",
        "name",
        "email",
        "country",
        "signup_date",
        "lifetime_value",
    ],
    "type_mapping": {
        "customer_id": "int",
        "signup_date": "datetime",
        "lifetime_value": "float",
    },
    "format_rules": {"email": r".*@.*"},
    "range_rules": {"customer_id": (1, 999999), "lifetime_value": (0, 50000)},
    "primary_key_columns": ["customer_id"],
    "unique_columns": ["email"],
    "consistency_rules": ["customer_id > 0", "lifetime_value >= 0"],
}

# Order Items Configuration
order_items_config = {
    "non_null_columns": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ],
    "expected_columns": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ],
    "type_mapping": {
        "order_item_id": "int",
        "order_id": "int",
        "product_id": "int",
        "quantity": "int",
        "unit_price": "float",
    },
    "range_rules": {
        "order_item_id": (1, 999999),
        "order_id": (1000, 999999),
        "product_id": (1, 999999),
        "quantity": (1, 100),
        "unit_price": (0, 10000),
    },
    "primary_key_columns": ["order_item_id"],
    "consistency_rules": [
        "order_item_id > 0",
        "order_id > 0",
        "product_id > 0",
        "quantity > 0",
        "unit_price > 0",
    ],
}

# Configuration mapping for batch processing
config_mapping = {
    "raw_customers.csv": raw_customer_config,
    "customers.csv": customers_config,
    "products.csv": products_config,
    "orders.csv": orders_config,
    "order_items.csv": order_items_config,
    "raw_customers_cleaned.csv": raw_customer_config
}