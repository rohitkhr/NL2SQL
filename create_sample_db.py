import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_sample_database():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to database (creates it if doesn't exist)
    conn = sqlite3.connect('data/sample_business.db')
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        city TEXT,
        state TEXT,
        registration_date DATE,
        customer_type TEXT CHECK(customer_type IN ('Premium', 'Standard', 'Basic'))
    )
    ''')
    
    # Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        price DECIMAL(10,2),
        stock_quantity INTEGER,
        supplier TEXT,
        created_date DATE
    )
    ''')
    
    # Orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date DATE,
        total_amount DECIMAL(10,2),
        status TEXT CHECK(status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
        shipping_city TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Order items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price DECIMAL(10,2),
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')
    
    print("Inserting sample data...")
    
    # Insert sample customers
    customers_data = [
        (1, 'John', 'Smith', 'john.smith@email.com', '555-1234', 'New York', 'NY', '2023-01-15', 'Premium'),
        (2, 'Sarah', 'Johnson', 'sarah.j@email.com', '555-2345', 'Los Angeles', 'CA', '2023-02-20', 'Standard'),
        (3, 'Mike', 'Davis', 'mike.davis@email.com', '555-3456', 'Chicago', 'IL', '2023-03-10', 'Basic'),
        (4, 'Emily', 'Wilson', 'emily.w@email.com', '555-4567', 'Houston', 'TX', '2023-04-05', 'Premium'),
        (5, 'Robert', 'Brown', 'robert.b@email.com', '555-5678', 'Phoenix', 'AZ', '2023-05-12', 'Standard'),
        (6, 'Lisa', 'Garcia', 'lisa.garcia@email.com', '555-6789', 'Philadelphia', 'PA', '2023-06-18', 'Basic'),
        (7, 'David', 'Martinez', 'david.m@email.com', '555-7890', 'San Antonio', 'TX', '2023-07-22', 'Premium'),
        (8, 'Jennifer', 'Anderson', 'jen.anderson@email.com', '555-8901', 'San Diego', 'CA', '2023-08-30', 'Standard')
    ]
    
    cursor.executemany('INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?,?,?,?)', customers_data)
    
    # Insert sample products
    products_data = [
        (1, 'Laptop Pro 15', 'Electronics', 1299.99, 50, 'TechCorp', '2023-01-01'),
        (2, 'Wireless Headphones', 'Electronics', 199.99, 100, 'AudioTech', '2023-01-15'),
        (3, 'Office Chair', 'Furniture', 299.99, 25, 'ComfortSeats', '2023-02-01'),
        (4, 'Smartphone X', 'Electronics', 799.99, 75, 'MobileTech', '2023-02-15'),
        (5, 'Standing Desk', 'Furniture', 399.99, 20, 'WorkSpace', '2023-03-01'),
        (6, 'Coffee Maker', 'Appliances', 129.99, 40, 'BrewMaster', '2023-03-15'),
        (7, 'Bluetooth Speaker', 'Electronics', 89.99, 60, 'SoundWave', '2023-04-01'),
        (8, 'Ergonomic Mouse', 'Electronics', 49.99, 80, 'InputDevices', '2023-04-15')
    ]
    
    cursor.executemany('INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?)', products_data)
    
    # Insert sample orders
    orders_data = [
        (1, 1, '2024-01-10', 1499.98, 'Delivered', 'New York'),
        (2, 2, '2024-01-15', 299.99, 'Delivered', 'Los Angeles'),
        (3, 3, '2024-01-20', 199.99, 'Shipped', 'Chicago'),
        (4, 1, '2024-02-01', 829.98, 'Delivered', 'New York'),
        (5, 4, '2024-02-05', 399.99, 'Delivered', 'Houston'),
        (6, 2, '2024-02-10', 179.98, 'Shipped', 'Los Angeles'),
        (7, 5, '2024-02-15', 1299.99, 'Pending', 'Phoenix'),
        (8, 3, '2024-03-01', 89.99, 'Delivered', 'Chicago')
    ]
    
    cursor.executemany('INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)', orders_data)
    
    # Insert sample order items
    order_items_data = [
        (1, 1, 1, 1, 1299.99),  # Order 1: 1 Laptop
        (2, 1, 2, 1, 199.99),   # Order 1: 1 Headphones
        (3, 2, 3, 1, 299.99),   # Order 2: 1 Chair
        (4, 3, 2, 1, 199.99),   # Order 3: 1 Headphones
        (5, 4, 4, 1, 799.99),   # Order 4: 1 Smartphone
        (6, 4, 8, 1, 49.99),    # Order 4: 1 Mouse (price difference due to discount)
        (7, 5, 5, 1, 399.99),   # Order 5: 1 Standing Desk
        (8, 6, 6, 1, 129.99),   # Order 6: 1 Coffee Maker
        (9, 6, 8, 1, 49.99),    # Order 6: 1 Mouse
        (10, 7, 1, 1, 1299.99), # Order 7: 1 Laptop
        (11, 8, 7, 1, 89.99)    # Order 8: 1 Speaker
    ]
    
    cursor.executemany('INSERT OR REPLACE INTO order_items VALUES (?,?,?,?,?)', order_items_data)
    
    # Commit and close
    conn.commit()
    
    # Show what we created
    print("\n=== Database Created Successfully! ===")
    print("\nTable summary:")
    
    # Count records in each table
    tables = ['customers', 'products', 'orders', 'order_items']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")
    
    print("\nSample queries you can try:")
    print("- 'Show me all customers'")
    print("- 'What are the total sales for each customer?'")
    print("- 'Show me all electronics products'")
    print("- 'Which customers are from California?'")
    print("- 'What orders were placed in February 2024?'")
    
    conn.close()
    print(f"\nDatabase saved as: data/sample_business.db")

if __name__ == "__main__":
    create_sample_database()