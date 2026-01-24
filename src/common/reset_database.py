import duckdb
import os

def reset_database():
    """Reset all tables by dropping and recreating them"""
    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )
    schema = "ecommerce"
    tables = ["customers", "products", "orders", "order_items", "raw_customers", "raw_customers","raw_products","raw_orders","raw_orders","raw_order_items","clean_customers"]

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


def clear_data_only(stage:str):
    """Clear data from tables without dropping them"""
    conn = duckdb.connect(
        os.getenv('DUCKDB_PATH', '/app/database/data_eng.db')
    )
    schema = "ecommerce"
    if stage == "bronze":
        tables = ["raw_customers_v2", "raw_products", "raw_orders", "_raw_order_items", "raw_customers"]

        try:
            # Create schema if it doesn't exist
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            
            # Create tables if they don't exist
            create_tables_if_not_exist(conn,stage)
            
            for table in tables:
                conn.execute(f"DELETE FROM {schema}.{table}")
                print(f"Cleared data from: {schema}.{table}")

            print("All table data cleared successfully")

        except Exception as e:
            print(f"Error clearing data: {e}")
        finally:
            conn.close()

    if stage =="silver":
        tables = ["customers", "products", "orders", "order_items", "clean_customers"]

        try:
            # Create schema if it doesn't exist
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            
            # Create tables if they don't exist
            create_tables_if_not_exist(conn,stage)
            
            for table in tables:
                conn.execute(f"DELETE FROM {schema}.{table}")
                print(f"Cleared data from: {schema}.{table}")

            print("All table data cleared successfully")

        except Exception as e:
            print(f"Error clearing data: {e}")
        finally:
            conn.close()
    


def create_tables_if_not_exist(conn,stage):
    """Create tables if they don't exist"""
    schema = "ecommerce"
    if stage == "silver":
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
            CREATE TABLE IF NOT EXISTS {schema}.clean_customers(
                customer_id INT, 
                name VARCHAR(255), 
                email VARCHAR(255), 
                phone VARCHAR(255), 
                age INT, 
                country VARCHAR(255), 
                signup_date DATE
            )
        """)
    if stage == "bronze":
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.raw_customers_v2(
                customer_id VARCHAR(255), 
                name VARCHAR(255), 
                email VARCHAR(255), 
                phone VARCHAR(255), 
                age VARCHAR(255), 
                country VARCHAR(255), 
                signup_date VARCHAR(255)
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.raw_products (
                product_id VARCHAR(255), 
                name VARCHAR(255),
                category VARCHAR(255),
                price VARCHAR(255),
                stock VARCHAR(255),
                supplier_id VARCHAR(255)
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.raw_orders(
                order_id VARCHAR(255), 
                customer_id VARCHAR(255), 
                order_date VARCHAR(255), 
                total_amount VARCHAR(255),
                status VARCHAR(255)
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}._raw_order_items(
                order_item_id VARCHAR(255),
                order_id VARCHAR(255),
                product_id VARCHAR(255),
                quantity VARCHAR(255),
                unit_price VARCHAR(255)
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.raw_customers(
                customer_id VARCHAR(255), 
                name VARCHAR(255), 
                email VARCHAR(255), 
                phone VARCHAR(255), 
                age VARCHAR(255), 
                country VARCHAR(255), 
                signup_date VARCHAR(255)
            )
        """)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear-only":
        clear_data_only(stage='bronze')
    else:
        reset_database()