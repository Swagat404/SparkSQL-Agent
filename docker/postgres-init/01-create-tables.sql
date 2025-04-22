-- Create sample tables for testing purposes

-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    sku VARCHAR(50) UNIQUE,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address VARCHAR(200),
    shipping_city VARCHAR(50),
    shipping_state VARCHAR(50),
    shipping_country VARCHAR(50),
    shipping_postal_code VARCHAR(20),
    shipping_method VARCHAR(50),
    payment_method VARCHAR(50),
    order_total DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(category_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product categories (many-to-many relationship)
CREATE TABLE product_categories (
    product_id INTEGER REFERENCES products(product_id),
    category_id INTEGER REFERENCES categories(category_id),
    PRIMARY KEY (product_id, category_id)
);

-- Employees table
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    job_title VARCHAR(50),
    department VARCHAR(50),
    manager_id INTEGER REFERENCES employees(employee_id),
    hire_date DATE,
    salary DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Regions table
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    country VARCHAR(50)
);

-- Stores table
CREATE TABLE stores (
    store_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region_id INTEGER REFERENCES regions(region_id),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    manager_id INTEGER REFERENCES employees(employee_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store inventory table
CREATE TABLE store_inventory (
    store_id INTEGER REFERENCES stores(store_id),
    product_id INTEGER REFERENCES products(product_id),
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (store_id, product_id)
);

-- Insert some sample data for regions
INSERT INTO regions (name, country) VALUES
('Northeast', 'USA'),
('Southeast', 'USA'),
('Midwest', 'USA'),
('West', 'USA'),
('Southwest', 'USA'),
('Northwest', 'USA'),
('Central', 'Canada'),
('East', 'Canada'),
('West', 'Canada');

-- Insert some sample data for categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Home & Kitchen', 'Household items and appliances'),
('Books', 'Books, e-books, and educational materials'),
('Toys & Games', 'Toys, games, and entertainment items');

-- Insert subcategories
INSERT INTO categories (name, description, parent_category_id) VALUES
('Smartphones', 'Mobile phones and accessories', 1),
('Laptops', 'Portable computers', 1),
('Men''s Clothing', 'Clothing for men', 2),
('Women''s Clothing', 'Clothing for women', 2),
('Kitchen Appliances', 'Appliances for the kitchen', 3),
('Fiction', 'Fictional books', 4),
('Non-Fiction', 'Non-fictional books', 4),
('Board Games', 'Tabletop games', 5);

-- Insert some sample data for products
INSERT INTO products (name, description, category, price, cost, sku, stock_quantity) VALUES
('iPhone 13', 'Latest iPhone model', 'Electronics', 999.99, 700.00, 'IPHONE13', 50),
('Samsung Galaxy S21', 'Latest Samsung smartphone', 'Electronics', 899.99, 650.00, 'GALAXYS21', 60),
('MacBook Pro', '16-inch laptop with M1 Pro', 'Electronics', 2499.99, 1800.00, 'MACBOOKPRO16', 25),
('Dell XPS 13', '13-inch ultrabook', 'Electronics', 1299.99, 900.00, 'DELLXPS13', 30),
('Men''s T-Shirt', 'Cotton t-shirt for men', 'Clothing', 19.99, 5.00, 'MENSTSHIRT', 200),
('Women''s Jeans', 'Slim fit jeans for women', 'Clothing', 49.99, 15.00, 'WOMENSJEANS', 150),
('Coffee Maker', 'Drip coffee maker', 'Home & Kitchen', 79.99, 30.00, 'COFFEEMAKER', 40),
('Blender', 'High-speed blender', 'Home & Kitchen', 129.99, 50.00, 'BLENDER', 35),
('Harry Potter Book Set', 'Complete set of Harry Potter books', 'Books', 99.99, 40.00, 'HARRYPOTTERSET', 15),
('Monopoly', 'Classic board game', 'Toys & Games', 24.99, 10.00, 'MONOPOLY', 50);

-- Link products to categories
INSERT INTO product_categories (product_id, category_id) VALUES
(1, 6), -- iPhone -> Smartphones
(2, 6), -- Galaxy -> Smartphones
(3, 7), -- MacBook -> Laptops
(4, 7), -- Dell XPS -> Laptops
(5, 8), -- Men's T-Shirt -> Men's Clothing
(6, 9), -- Women's Jeans -> Women's Clothing
(7, 10), -- Coffee Maker -> Kitchen Appliances
(8, 10), -- Blender -> Kitchen Appliances
(9, 11), -- Harry Potter -> Fiction
(10, 13); -- Monopoly -> Board Games

-- Insert some sample data for employees
INSERT INTO employees (first_name, last_name, email, job_title, department, hire_date, salary) VALUES
('John', 'Smith', 'john.smith@example.com', 'CEO', 'Executive', '2015-01-01', 200000.00),
('Jane', 'Doe', 'jane.doe@example.com', 'CFO', 'Finance', '2015-02-15', 180000.00),
('Bob', 'Johnson', 'bob.johnson@example.com', 'CTO', 'Technology', '2015-03-10', 180000.00),
('Alice', 'Williams', 'alice.williams@example.com', 'VP Sales', 'Sales', '2016-01-15', 150000.00),
('Charlie', 'Brown', 'charlie.brown@example.com', 'VP Marketing', 'Marketing', '2016-02-20', 150000.00);

-- Update manager IDs
UPDATE employees SET manager_id = 1 WHERE employee_id IN (2, 3, 4, 5);

-- Insert more employees with managers
INSERT INTO employees (first_name, last_name, email, job_title, department, manager_id, hire_date, salary) VALUES
('David', 'Miller', 'david.miller@example.com', 'Store Manager', 'Retail', 4, '2017-03-15', 80000.00),
('Sarah', 'Wilson', 'sarah.wilson@example.com', 'Store Manager', 'Retail', 4, '2017-04-20', 80000.00),
('Michael', 'Davis', 'michael.davis@example.com', 'Store Manager', 'Retail', 4, '2017-05-25', 80000.00),
('Emily', 'Garcia', 'emily.garcia@example.com', 'Store Manager', 'Retail', 4, '2017-06-30', 80000.00),
('Daniel', 'Rodriguez', 'daniel.rodriguez@example.com', 'Store Manager', 'Retail', 4, '2017-07-05', 80000.00);

-- Insert some sample data for stores
INSERT INTO stores (name, region_id, address, city, state, country, postal_code, manager_id) VALUES
('New York Store', 1, '123 Broadway', 'New York', 'NY', 'USA', '10001', 6),
('Atlanta Store', 2, '456 Peachtree St', 'Atlanta', 'GA', 'USA', '30303', 7),
('Chicago Store', 3, '789 Michigan Ave', 'Chicago', 'IL', 'USA', '60601', 8),
('Los Angeles Store', 4, '321 Hollywood Blvd', 'Los Angeles', 'CA', 'USA', '90001', 9),
('Phoenix Store', 5, '654 Desert Rd', 'Phoenix', 'AZ', 'USA', '85001', 10);

-- Insert some sample data for store inventory
INSERT INTO store_inventory (store_id, product_id, stock_quantity) VALUES
(1, 1, 10), -- iPhone in New York
(1, 2, 12), -- Galaxy in New York
(1, 3, 5),  -- MacBook in New York
(1, 4, 6),  -- Dell XPS in New York
(1, 5, 40), -- Men's T-Shirt in New York
(2, 1, 8),  -- iPhone in Atlanta
(2, 2, 10), -- Galaxy in Atlanta
(2, 3, 4),  -- MacBook in Atlanta
(2, 4, 5),  -- Dell XPS in Atlanta
(2, 5, 35), -- Men's T-Shirt in Atlanta
(3, 1, 9),  -- iPhone in Chicago
(3, 2, 11), -- Galaxy in Chicago
(3, 3, 5),  -- MacBook in Chicago
(3, 4, 6),  -- Dell XPS in Chicago
(3, 5, 38), -- Men's T-Shirt in Chicago
(4, 1, 12), -- iPhone in Los Angeles
(4, 2, 15), -- Galaxy in Los Angeles
(4, 3, 7),  -- MacBook in Los Angeles
(4, 4, 8),  -- Dell XPS in Los Angeles
(4, 5, 45), -- Men's T-Shirt in Los Angeles
(5, 1, 7),  -- iPhone in Phoenix
(5, 2, 9),  -- Galaxy in Phoenix
(5, 3, 3),  -- MacBook in Phoenix
(5, 4, 4),  -- Dell XPS in Phoenix
(5, 5, 30); -- Men's T-Shirt in Phoenix

-- Insert some sample data for customers
INSERT INTO customers (first_name, last_name, email, phone, address, city, state, country, postal_code) VALUES
('Mary', 'Johnson', 'mary.johnson@example.com', '555-123-4567', '123 Main St', 'New York', 'NY', 'USA', '10001'),
('James', 'Smith', 'james.smith@example.com', '555-234-5678', '456 Elm St', 'Los Angeles', 'CA', 'USA', '90001'),
('Patricia', 'Williams', 'patricia.williams@example.com', '555-345-6789', '789 Oak St', 'Chicago', 'IL', 'USA', '60601'),
('Robert', 'Brown', 'robert.brown@example.com', '555-456-7890', '321 Pine St', 'Houston', 'TX', 'USA', '77001'),
('Jennifer', 'Jones', 'jennifer.jones@example.com', '555-567-8901', '654 Maple St', 'Phoenix', 'AZ', 'USA', '85001'),
('Michael', 'Miller', 'michael.miller@example.com', '555-678-9012', '987 Cedar St', 'Philadelphia', 'PA', 'USA', '19101'),
('Linda', 'Davis', 'linda.davis@example.com', '555-789-0123', '159 Birch St', 'San Antonio', 'TX', 'USA', '78201'),
('William', 'Garcia', 'william.garcia@example.com', '555-890-1234', '357 Walnut St', 'San Diego', 'CA', 'USA', '92101'),
('Elizabeth', 'Rodriguez', 'elizabeth.rodriguez@example.com', '555-901-2345', '753 Spruce St', 'Dallas', 'TX', 'USA', '75201'),
('David', 'Wilson', 'david.wilson@example.com', '555-012-3456', '951 Fir St', 'San Jose', 'CA', 'USA', '95101');

-- Insert some sample data for orders
INSERT INTO orders (customer_id, order_date, status, shipping_address, shipping_city, shipping_state, shipping_country, shipping_postal_code, shipping_method, payment_method, order_total) VALUES
(1, '2023-01-15 10:30:00', 'completed', '123 Main St', 'New York', 'NY', 'USA', '10001', 'Standard', 'Credit Card', 1049.98),
(2, '2023-01-20 11:45:00', 'completed', '456 Elm St', 'Los Angeles', 'CA', 'USA', '90001', 'Express', 'PayPal', 2599.98),
(3, '2023-01-25 14:20:00', 'completed', '789 Oak St', 'Chicago', 'IL', 'USA', '60601', 'Standard', 'Credit Card', 249.95),
(4, '2023-02-05 09:15:00', 'completed', '321 Pine St', 'Houston', 'TX', 'USA', '77001', 'Standard', 'Credit Card', 129.99),
(5, '2023-02-10 16:30:00', 'completed', '654 Maple St', 'Phoenix', 'AZ', 'USA', '85001', 'Express', 'PayPal', 174.95),
(1, '2023-02-15 13:45:00', 'shipped', '123 Main St', 'New York', 'NY', 'USA', '10001', 'Standard', 'Credit Card', 1399.98),
(2, '2023-02-20 10:30:00', 'shipped', '456 Elm St', 'Los Angeles', 'CA', 'USA', '90001', 'Express', 'PayPal', 929.98),
(3, '2023-02-25 15:20:00', 'shipped', '789 Oak St', 'Chicago', 'IL', 'USA', '60601', 'Standard', 'Credit Card', 99.99),
(4, '2023-03-05 08:15:00', 'processing', '321 Pine St', 'Houston', 'TX', 'USA', '77001', 'Standard', 'Credit Card', 2524.98),
(5, '2023-03-10 17:30:00', 'processing', '654 Maple St', 'Phoenix', 'AZ', 'USA', '85001', 'Express', 'PayPal', 149.98);

-- Insert some sample data for order items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 999.99), -- iPhone for order 1
(1, 5, 2, 19.99),  -- Men's T-Shirt for order 1
(2, 3, 1, 2499.99), -- MacBook Pro for order 2
(2, 10, 4, 24.99), -- Monopoly for order 2
(3, 5, 5, 19.99), -- Men's T-Shirt for order 3
(3, 10, 6, 24.99), -- Monopoly for order 3
(4, 8, 1, 129.99), -- Blender for order 4
(5, 6, 2, 49.99), -- Women's Jeans for order 5
(5, 10, 3, 24.99), -- Monopoly for order 5
(6, 4, 1, 1299.99), -- Dell XPS for order 6
(6, 5, 5, 19.99), -- Men's T-Shirt for order 6
(7, 2, 1, 899.99), -- Galaxy for order 7
(7, 7, 1, 79.99), -- Coffee Maker for order 7
(8, 9, 1, 99.99), -- Harry Potter for order 8
(9, 3, 1, 2499.99), -- MacBook Pro for order 9
(9, 5, 1, 19.99), -- Men's T-Shirt for order 9
(9, 10, 1, 24.99), -- Monopoly for order 9
(10, 6, 3, 49.99); -- Women's Jeans for order 10 