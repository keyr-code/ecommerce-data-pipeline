import duckdb
import os


def reset_database():
    """Reset all tables by dropping and recreating them"""
    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )
    schema = "ecommerce"
    tables = ["customers", "products", "orders", "order_items", "raw_customers"]

    try:
        # Create schema if it doesn't exist
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        print(f"Schema {schema} created/verified")
        
        # Drop existing tables
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {schema}.{table}")
            print(f"Dropped table: {schema}.{table}")

        # Recreate tables with proper schema
        conn.execute(
            f"""
            CREATE TABLE {schema}.customers(
                customer_id INT,
                name VARCHAR(255),
                email VARCHAR(255),
                country VARCHAR(255),
                signup_date DATE,
                lifetime_value FLOAT
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE {schema}.products (
                product_id INT, 
                name VARCHAR(255),
                category VARCHAR(255),
                price FLOAT,
                stock INT,
                supplier_id INT
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE {schema}.orders(
                order_id INT, 
                customer_id INT, 
                order_date DATE, 
                total_amount FLOAT,
                status VARCHAR(255)
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE {schema}.order_items(
                order_item_id INT,
                order_id INT,
                product_id INT,
                quantity INT,
                unit_price FLOAT
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE {schema}.raw_customers(
                customer_id INT, 
                name VARCHAR(255), 
                email VARCHAR(255), 
                phone VARCHAR(255), 
                age INT, 
                country VARCHAR(255), 
                signup_date DATE
            )
        """
        )

        print("All tables recreated successfully")

    except Exception as e:
        print(f"Error resetting database: {e}")
    finally:
        conn.close()


def clear_data_only():
    """Clear data from tables without dropping them"""
    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )
    schema = "ecommerce"
    tables = ["customers", "products", "orders", "order_items", "raw_customers"]

    try:
        # Create schema if it doesn't exist
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        
        # Create tables if they don't exist
        create_tables_if_not_exist(conn)
        
        for table in tables:
            conn.execute(f"DELETE FROM {schema}.{table}")
            print(f"Cleared data from: {schema}.{table}")

        print("All table data cleared successfully")

    except Exception as e:
        print(f"Error clearing data: {e}")
    finally:
        conn.close()


def create_tables_if_not_exist(conn):
    """Create tables if they don't exist"""
    schema = "ecommerce"
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.customers(
            customer_id INT,
            name VARCHAR(255),
            email VARCHAR(255),
            country VARCHAR(255),
            signup_date DATE,
            lifetime_value FLOAT
        )
    """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.products (
            product_id INT, 
            name VARCHAR(255),
            category VARCHAR(255),
            price FLOAT,
            stock INT,
            supplier_id INT
        )
    """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.orders(
            order_id INT, 
            customer_id INT, 
            order_date DATE, 
            total_amount FLOAT,
            status VARCHAR(255)
        )
    """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.order_items(
            order_item_id INT,
            order_id INT,
            product_id INT,
            quantity INT,
            unit_price FLOAT
        )
    """
    )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.raw_customers(
            customer_id INT, 
            name VARCHAR(255), 
            email VARCHAR(255), 
            phone VARCHAR(255), 
            age INT, 
            country VARCHAR(255), 
            signup_date DATE
        )
    """)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear-only":
        clear_data_only()
    else:
        reset_database()