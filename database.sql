DROP TABLE IF EXISTS shop_items;
DROP TABLE IF EXISTS carts;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS orders;

CREATE TABLE categories (
name varchar(255) UNIQUE NOT NULL
);

CREATE TABLE shop_items (
item_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
item_name varchar(255),
price INTEGER,
ingredients TEXT,
category VARCHAR(255) REFERENCES categories (name),
photo_path VARCHAR(255),
nutrition_facts VARCHAR(255),
shelf_life VARCHAR(255),
weight VARCHAR(255)
);

CREATE TABLE carts (
user_id bigint
product_name varchar(255) REFERENCES shop_items (item_name)
quantity bigint
);

CREATE TABLE orders (
order_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
user_id BIGINT,
order_items TEXT,
order_type VARCHAR(255),
order_status VARCHAR(255),
created_at DATE,
total_cost BIGINT,
user_name VARCHAR(255),
user_phone VARCHAR(255),
user_address VARCHAR(255)
)
