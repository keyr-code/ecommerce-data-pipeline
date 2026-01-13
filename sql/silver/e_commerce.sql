CREATE table customers(
customer_id int,
name VARCHAR(255),
email VARCHAR(255),
country VARCHAR(255),
signup_date DATE,
lifetime_value FLOAT
)

CREATE table products (
product_id int, 
name VARCHAR(255),
category VARCHAR(255),
price FLOAT,
stock int,
supplier_id int
)

CREATE table orders(
order_id int, 
customer_id int, 
order_date DATE, 
total_amount FLOAT,
status VARCHAR(255)
)

CREATE table order_items(
order_item_id INT,
order_id int,
product_id int,
quantity int,
unit_price FLOAT
)

CREATE table raw_customers(
customer_id INT,
name VARCHAR(255),
email VARCHAR(255),
phone VARCHAR(255),
age INT,
country VARCHAR(255),
signup_date DATE
)