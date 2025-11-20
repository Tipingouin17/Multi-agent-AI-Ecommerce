-- ============================================================================
-- SEED DATA SCRIPT - PART 1: CORE DATA
-- ============================================================================
-- This script populates core tables with realistic test data
-- Run after all migrations are complete
-- ============================================================================

-- Clear existing data (optional - comment out for production)
-- TRUNCATE TABLE users, customers, products, orders CASCADE;

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

-- Admin Users
INSERT INTO users (id, email, username, password_hash, role, first_name, last_name, phone, is_active, created_at) VALUES
(1, 'admin@ecommerce.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'admin', 'John', 'Admin', '+1234567890', true, NOW() - INTERVAL '365 days'),
(2, 'superadmin@ecommerce.com', 'superadmin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'admin', 'Sarah', 'SuperAdmin', '+1234567891', true, NOW() - INTERVAL '365 days');

-- Merchant Users
INSERT INTO users (id, email, username, password_hash, role, first_name, last_name, phone, is_active, created_at) VALUES
(3, 'merchant1@example.com', 'merchant1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'merchant', 'Mike', 'Merchant', '+1234567892', true, NOW() - INTERVAL '180 days'),
(4, 'merchant2@example.com', 'merchant2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'merchant', 'Mary', 'Seller', '+1234567893', true, NOW() - INTERVAL '150 days');

-- Customer Users (10 customers)
INSERT INTO users (id, email, username, password_hash, role, first_name, last_name, phone, is_active, created_at) VALUES
(11, 'customer1@example.com', 'customer1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Alice', 'Johnson', '+1234567900', true, NOW() - INTERVAL '200 days'),
(12, 'customer2@example.com', 'customer2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Bob', 'Smith', '+1234567901', true, NOW() - INTERVAL '180 days'),
(13, 'customer3@example.com', 'customer3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Carol', 'Williams', '+1234567902', true, NOW() - INTERVAL '160 days'),
(14, 'customer4@example.com', 'customer4', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'David', 'Brown', '+1234567903', true, NOW() - INTERVAL '140 days'),
(15, 'customer5@example.com', 'customer5', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Emma', 'Davis', '+1234567904', true, NOW() - INTERVAL '120 days'),
(16, 'customer6@example.com', 'customer6', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Frank', 'Miller', '+1234567905', true, NOW() - INTERVAL '100 days'),
(17, 'customer7@example.com', 'customer7', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Grace', 'Wilson', '+1234567906', true, NOW() - INTERVAL '80 days'),
(18, 'customer8@example.com', 'customer8', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Henry', 'Moore', '+1234567907', true, NOW() - INTERVAL '60 days'),
(19, 'customer9@example.com', 'customer9', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Ivy', 'Taylor', '+1234567908', true, NOW() - INTERVAL '40 days'),
(20, 'customer10@example.com', 'customer10', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebfeO', 'customer', 'Jack', 'Anderson', '+1234567909', true, NOW() - INTERVAL '20 days');

-- Update sequence
SELECT setval('users_id_seq', 20);

-- ============================================================================
-- CUSTOMERS
-- ============================================================================

INSERT INTO customers (id, user_id, email, first_name, last_name, phone, date_of_birth, loyalty_points, total_orders, total_spent, created_at) VALUES
(1, 11, 'customer1@example.com', 'Alice', 'Johnson', '+1234567900', '1990-05-15', 1250, 15, 2450.00, NOW() - INTERVAL '200 days'),
(2, 12, 'customer2@example.com', 'Bob', 'Smith', '+1234567901', '1985-08-22', 890, 12, 1780.00, NOW() - INTERVAL '180 days'),
(3, 13, 'customer3@example.com', 'Carol', 'Williams', '+1234567902', '1992-03-10', 2100, 25, 4200.00, NOW() - INTERVAL '160 days'),
(4, 14, 'customer4@example.com', 'David', 'Brown', '+1234567903', '1988-11-30', 450, 8, 900.00, NOW() - INTERVAL '140 days'),
(5, 15, 'customer5@example.com', 'Emma', 'Davis', '+1234567904', '1995-07-18', 1650, 18, 3300.00, NOW() - INTERVAL '120 days'),
(6, 16, 'customer6@example.com', 'Frank', 'Miller', '+1234567905', '1987-02-25', 320, 5, 640.00, NOW() - INTERVAL '100 days'),
(7, 17, 'customer7@example.com', 'Grace', 'Wilson', '+1234567906', '1993-09-12', 980, 14, 1960.00, NOW() - INTERVAL '80 days'),
(8, 18, 'customer8@example.com', 'Henry', 'Moore', '+1234567907', '1991-04-08', 1120, 16, 2240.00, NOW() - INTERVAL '60 days'),
(9, 19, 'customer9@example.com', 'Ivy', 'Taylor', '+1234567908', '1989-12-20', 560, 9, 1120.00, NOW() - INTERVAL '40 days'),
(10, 20, 'customer10@example.com', 'Jack', 'Anderson', '+1234567909', '1994-06-05', 780, 11, 1560.00, NOW() - INTERVAL '20 days');

SELECT setval('customers_id_seq', 10);

-- ============================================================================
-- WAREHOUSES
-- ============================================================================

INSERT INTO warehouses (id, name, code, address, city, state, country, postal_code, capacity, current_utilization, is_active, created_at) VALUES
(1, 'Main Warehouse - East Coast', 'WH-EAST-01', '123 Industrial Blvd', 'New York', 'NY', 'USA', '10001', 50000, 32500, true, NOW() - INTERVAL '365 days'),
(2, 'West Coast Distribution Center', 'WH-WEST-01', '456 Logistics Ave', 'Los Angeles', 'CA', 'USA', '90001', 75000, 45000, true, NOW() - INTERVAL '365 days'),
(3, 'Midwest Fulfillment Center', 'WH-MIDWEST-01', '789 Commerce Dr', 'Chicago', 'IL', 'USA', '60601', 60000, 38000, true, NOW() - INTERVAL '300 days'),
(4, 'Southern Distribution Hub', 'WH-SOUTH-01', '321 Supply Chain Rd', 'Dallas', 'TX', 'USA', '75201', 55000, 28000, true, NOW() - INTERVAL '250 days');

SELECT setval('warehouses_id_seq', 4);

-- ============================================================================
-- SUPPLIERS
-- ============================================================================

INSERT INTO suppliers (id, name, code, contact_name, email, phone, address, city, state, country, postal_code, payment_terms, lead_time_days, minimum_order_value, rating, is_active, created_at) VALUES
(1, 'TechGear Wholesale Inc', 'SUP-TECH-001', 'James Wilson', 'james@techgear.com', '+1555001001', '100 Tech Park', 'San Francisco', 'CA', 'USA', '94102', 'Net 30', 14, 1000.00, 4.5, true, NOW() - INTERVAL '365 days'),
(2, 'Fashion Forward Distributors', 'SUP-FASH-001', 'Linda Chen', 'linda@fashionforward.com', '+1555002002', '200 Fashion Ave', 'New York', 'NY', 'USA', '10018', 'Net 45', 21, 2000.00, 4.8, true, NOW() - INTERVAL '365 days'),
(3, 'Home Essentials Supply Co', 'SUP-HOME-001', 'Robert Martinez', 'robert@homeessentials.com', '+1555003003', '300 Home Goods Ln', 'Atlanta', 'GA', 'USA', '30303', 'Net 30', 10, 500.00, 4.2, true, NOW() - INTERVAL '300 days'),
(4, 'Sports & Outdoors Wholesale', 'SUP-SPORT-001', 'Maria Garcia', 'maria@sportsoutdoors.com', '+1555004004', '400 Athletic Way', 'Denver', 'CO', 'USA', '80202', 'Net 60', 28, 1500.00, 4.6, true, NOW() - INTERVAL '250 days'),
(5, 'Beauty Products International', 'SUP-BEAUTY-001', 'Sarah Kim', 'sarah@beautyproducts.com', '+1555005005', '500 Cosmetics Blvd', 'Miami', 'FL', 'USA', '33101', 'Net 30', 18, 800.00, 4.7, true, NOW() - INTERVAL '200 days');

SELECT setval('suppliers_id_seq', 5);

-- ============================================================================
-- PRODUCTS (50 products across categories)
-- ============================================================================

-- Electronics (10 products)
INSERT INTO products (id, sku, name, description, category, price, cost, stock_quantity, warehouse_id, supplier_id, is_active, created_at) VALUES
(1, 'ELEC-LAP-001', 'Premium Laptop 15"', 'High-performance laptop with 16GB RAM, 512GB SSD', 'Electronics', 1299.99, 850.00, 45, 1, 1, true, NOW() - INTERVAL '300 days'),
(2, 'ELEC-PHONE-001', 'Smartphone Pro Max', 'Latest flagship smartphone with 5G', 'Electronics', 999.99, 650.00, 78, 1, 1, true, NOW() - INTERVAL '280 days'),
(3, 'ELEC-TAB-001', 'Tablet 10" WiFi', '10-inch tablet with WiFi connectivity', 'Electronics', 449.99, 280.00, 92, 1, 1, true, NOW() - INTERVAL '260 days'),
(4, 'ELEC-WATCH-001', 'Smart Watch Series 5', 'Fitness tracking smartwatch', 'Electronics', 349.99, 210.00, 125, 2, 1, true, NOW() - INTERVAL '240 days'),
(5, 'ELEC-HEADPHONE-001', 'Wireless Noise-Cancelling Headphones', 'Premium audio experience', 'Electronics', 299.99, 180.00, 156, 2, 1, true, NOW() - INTERVAL '220 days'),
(6, 'ELEC-SPEAKER-001', 'Bluetooth Speaker Waterproof', 'Portable waterproof speaker', 'Electronics', 89.99, 45.00, 234, 2, 1, true, NOW() - INTERVAL '200 days'),
(7, 'ELEC-CAMERA-001', 'Digital Camera 24MP', 'Professional digital camera', 'Electronics', 699.99, 420.00, 34, 1, 1, true, NOW() - INTERVAL '180 days'),
(8, 'ELEC-DRONE-001', 'Quadcopter Drone with Camera', '4K camera drone', 'Electronics', 499.99, 300.00, 28, 1, 1, true, NOW() - INTERVAL '160 days'),
(9, 'ELEC-CONSOLE-001', 'Gaming Console Next-Gen', 'Latest gaming console', 'Electronics', 499.99, 320.00, 67, 2, 1, true, NOW() - INTERVAL '140 days'),
(10, 'ELEC-MONITOR-001', '27" 4K Monitor', 'Ultra HD 4K monitor', 'Electronics', 399.99, 240.00, 54, 2, 1, true, NOW() - INTERVAL '120 days');

-- Fashion (10 products)
INSERT INTO products (id, sku, name, description, category, price, cost, stock_quantity, warehouse_id, supplier_id, is_active, created_at) VALUES
(11, 'FASH-JEANS-001', 'Classic Blue Jeans', 'Comfortable slim-fit jeans', 'Fashion', 79.99, 35.00, 345, 3, 2, true, NOW() - INTERVAL '250 days'),
(12, 'FASH-TSHIRT-001', 'Cotton T-Shirt Pack (3)', 'Premium cotton t-shirts', 'Fashion', 39.99, 15.00, 567, 3, 2, true, NOW() - INTERVAL '240 days'),
(13, 'FASH-DRESS-001', 'Summer Floral Dress', 'Elegant summer dress', 'Fashion', 89.99, 40.00, 234, 3, 2, true, NOW() - INTERVAL '230 days'),
(14, 'FASH-JACKET-001', 'Leather Jacket', 'Genuine leather jacket', 'Fashion', 249.99, 120.00, 89, 3, 2, true, NOW() - INTERVAL '220 days'),
(15, 'FASH-SHOES-001', 'Running Shoes', 'Comfortable running shoes', 'Fashion', 119.99, 55.00, 456, 4, 2, true, NOW() - INTERVAL '210 days'),
(16, 'FASH-SNEAKERS-001', 'Casual Sneakers', 'Stylish casual sneakers', 'Fashion', 89.99, 40.00, 678, 4, 2, true, NOW() - INTERVAL '200 days'),
(17, 'FASH-HANDBAG-001', 'Designer Handbag', 'Luxury designer handbag', 'Fashion', 199.99, 90.00, 123, 3, 2, true, NOW() - INTERVAL '190 days'),
(18, 'FASH-WATCH-001', 'Fashion Watch', 'Elegant fashion watch', 'Fashion', 149.99, 65.00, 234, 3, 2, true, NOW() - INTERVAL '180 days'),
(19, 'FASH-SUNGLASSES-001', 'Polarized Sunglasses', 'UV protection sunglasses', 'Fashion', 59.99, 25.00, 456, 3, 2, true, NOW() - INTERVAL '170 days'),
(20, 'FASH-BELT-001', 'Leather Belt', 'Genuine leather belt', 'Fashion', 39.99, 15.00, 789, 3, 2, true, NOW() - INTERVAL '160 days');

-- Home & Living (10 products)
INSERT INTO products (id, sku, name, description, category, price, cost, stock_quantity, warehouse_id, supplier_id, is_active, created_at) VALUES
(21, 'HOME-BEDDING-001', 'Queen Size Bedding Set', 'Luxury bedding set', 'Home & Living', 129.99, 60.00, 234, 4, 3, true, NOW() - INTERVAL '200 days'),
(22, 'HOME-TOWEL-001', 'Bath Towel Set (6 pieces)', 'Premium cotton towels', 'Home & Living', 49.99, 20.00, 456, 4, 3, true, NOW() - INTERVAL '190 days'),
(23, 'HOME-LAMP-001', 'Modern Table Lamp', 'LED table lamp', 'Home & Living', 69.99, 30.00, 345, 4, 3, true, NOW() - INTERVAL '180 days'),
(24, 'HOME-CURTAIN-001', 'Blackout Curtains', 'Room darkening curtains', 'Home & Living', 59.99, 25.00, 567, 4, 3, true, NOW() - INTERVAL '170 days'),
(25, 'HOME-RUG-001', 'Area Rug 5x7', 'Decorative area rug', 'Home & Living', 149.99, 70.00, 123, 4, 3, true, NOW() - INTERVAL '160 days'),
(26, 'HOME-PILLOW-001', 'Memory Foam Pillow', 'Ergonomic pillow', 'Home & Living', 39.99, 15.00, 678, 4, 3, true, NOW() - INTERVAL '150 days'),
(27, 'HOME-COOKWARE-001', 'Non-Stick Cookware Set', '10-piece cookware set', 'Home & Living', 199.99, 90.00, 234, 4, 3, true, NOW() - INTERVAL '140 days'),
(28, 'HOME-ORGANIZER-001', 'Storage Organizer', 'Multi-compartment organizer', 'Home & Living', 29.99, 12.00, 890, 4, 3, true, NOW() - INTERVAL '130 days'),
(29, 'HOME-MIRROR-001', 'Wall Mirror 24x36', 'Decorative wall mirror', 'Home & Living', 89.99, 40.00, 156, 4, 3, true, NOW() - INTERVAL '120 days'),
(30, 'HOME-CLOCK-001', 'Digital Alarm Clock', 'Smart alarm clock', 'Home & Living', 34.99, 15.00, 567, 4, 3, true, NOW() - INTERVAL '110 days');

-- Sports & Outdoors (10 products)
INSERT INTO products (id, sku, name, description, category, price, cost, stock_quantity, warehouse_id, supplier_id, is_active, created_at) VALUES
(31, 'SPORT-YOGA-001', 'Yoga Mat Premium', 'Non-slip yoga mat', 'Sports & Outdoors', 49.99, 20.00, 456, 2, 4, true, NOW() - INTERVAL '180 days'),
(32, 'SPORT-DUMBBELL-001', 'Adjustable Dumbbells', 'Set of adjustable dumbbells', 'Sports & Outdoors', 199.99, 90.00, 123, 2, 4, true, NOW() - INTERVAL '170 days'),
(33, 'SPORT-BIKE-001', 'Mountain Bike 26"', 'All-terrain mountain bike', 'Sports & Outdoors', 599.99, 320.00, 45, 2, 4, true, NOW() - INTERVAL '160 days'),
(34, 'SPORT-TENT-001', 'Camping Tent 4-Person', 'Waterproof camping tent', 'Sports & Outdoors', 149.99, 70.00, 89, 2, 4, true, NOW() - INTERVAL '150 days'),
(35, 'SPORT-BACKPACK-001', 'Hiking Backpack 40L', 'Durable hiking backpack', 'Sports & Outdoors', 89.99, 40.00, 234, 2, 4, true, NOW() - INTERVAL '140 days'),
(36, 'SPORT-BALL-001', 'Basketball Official Size', 'Professional basketball', 'Sports & Outdoors', 29.99, 12.00, 567, 2, 4, true, NOW() - INTERVAL '130 days'),
(37, 'SPORT-RACKET-001', 'Tennis Racket Pro', 'Professional tennis racket', 'Sports & Outdoors', 129.99, 60.00, 156, 2, 4, true, NOW() - INTERVAL '120 days'),
(38, 'SPORT-FISHING-001', 'Fishing Rod & Reel Combo', 'Complete fishing set', 'Sports & Outdoors', 79.99, 35.00, 234, 2, 4, true, NOW() - INTERVAL '110 days'),
(39, 'SPORT-SKATEBOARD-001', 'Complete Skateboard', 'Professional skateboard', 'Sports & Outdoors', 99.99, 45.00, 178, 2, 4, true, NOW() - INTERVAL '100 days'),
(40, 'SPORT-HELMET-001', 'Bike Helmet Safety', 'Protective bike helmet', 'Sports & Outdoors', 49.99, 20.00, 345, 2, 4, true, NOW() - INTERVAL '90 days');

-- Beauty & Personal Care (10 products)
INSERT INTO products (id, sku, name, description, category, price, cost, stock_quantity, warehouse_id, supplier_id, is_active, created_at) VALUES
(41, 'BEAUTY-SKINCARE-001', 'Anti-Aging Serum', 'Premium anti-aging serum', 'Beauty & Personal Care', 79.99, 35.00, 456, 3, 5, true, NOW() - INTERVAL '150 days'),
(42, 'BEAUTY-MAKEUP-001', 'Makeup Palette Pro', 'Professional makeup palette', 'Beauty & Personal Care', 59.99, 25.00, 567, 3, 5, true, NOW() - INTERVAL '140 days'),
(43, 'BEAUTY-PERFUME-001', 'Luxury Perfume 100ml', 'Designer fragrance', 'Beauty & Personal Care', 129.99, 60.00, 234, 3, 5, true, NOW() - INTERVAL '130 days'),
(44, 'BEAUTY-HAIR-001', 'Hair Dryer Professional', 'Ionic hair dryer', 'Beauty & Personal Care', 89.99, 40.00, 345, 3, 5, true, NOW() - INTERVAL '120 days'),
(45, 'BEAUTY-SHAMPOO-001', 'Organic Shampoo & Conditioner', 'Natural hair care set', 'Beauty & Personal Care', 39.99, 15.00, 678, 3, 5, true, NOW() - INTERVAL '110 days'),
(46, 'BEAUTY-LOTION-001', 'Body Lotion Moisturizing', 'Hydrating body lotion', 'Beauty & Personal Care', 24.99, 10.00, 890, 3, 5, true, NOW() - INTERVAL '100 days'),
(47, 'BEAUTY-BRUSH-001', 'Makeup Brush Set', '12-piece brush set', 'Beauty & Personal Care', 49.99, 20.00, 456, 3, 5, true, NOW() - INTERVAL '90 days'),
(48, 'BEAUTY-NAIL-001', 'Nail Polish Set', '10 colors nail polish', 'Beauty & Personal Care', 34.99, 15.00, 567, 3, 5, true, NOW() - INTERVAL '80 days'),
(49, 'BEAUTY-FACIAL-001', 'Facial Cleanser Set', 'Complete facial care', 'Beauty & Personal Care', 44.99, 18.00, 678, 3, 5, true, NOW() - INTERVAL '70 days'),
(50, 'BEAUTY-MASK-001', 'Face Mask Variety Pack', '20 sheet masks', 'Beauty & Personal Care', 29.99, 12.00, 789, 3, 5, true, NOW() - INTERVAL '60 days');

SELECT setval('products_id_seq', 50);

-- ============================================================================
-- PRODUCT IMAGES
-- ============================================================================

-- Add images for first 10 products (can be expanded)
INSERT INTO product_images (product_id, image_url, alt_text, is_primary, display_order, created_at) VALUES
(1, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853', 'Premium Laptop Front View', true, 1, NOW()),
(1, 'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2', 'Premium Laptop Side View', false, 2, NOW()),
(2, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9', 'Smartphone Pro Max', true, 1, NOW()),
(3, 'https://images.unsplash.com/photo-1561154464-82e9adf32764', 'Tablet 10 inch', true, 1, NOW()),
(4, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30', 'Smart Watch', true, 1, NOW()),
(5, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e', 'Wireless Headphones', true, 1, NOW()),
(6, 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1', 'Bluetooth Speaker', true, 1, NOW()),
(7, 'https://images.unsplash.com/photo-1502920917128-1aa500764cbd', 'Digital Camera', true, 1, NOW()),
(8, 'https://images.unsplash.com/photo-1473968512647-3e447244af8f', 'Quadcopter Drone', true, 1, NOW()),
(9, 'https://images.unsplash.com/photo-1486401899868-0e435ed85128', 'Gaming Console', true, 1, NOW()),
(10, 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf', '4K Monitor', true, 1, NOW());

-- ============================================================================
-- INVENTORY
-- ============================================================================

-- Inventory records for all products
INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, reorder_point, reorder_quantity, last_restock_date, updated_at) VALUES
(1, 1, 45, 5, 10, 20, NOW() - INTERVAL '30 days', NOW()),
(2, 1, 78, 8, 15, 30, NOW() - INTERVAL '25 days', NOW()),
(3, 1, 92, 10, 20, 40, NOW() - INTERVAL '20 days', NOW()),
(4, 2, 125, 15, 25, 50, NOW() - INTERVAL '15 days', NOW()),
(5, 2, 156, 18, 30, 60, NOW() - INTERVAL '10 days', NOW()),
(6, 2, 234, 25, 40, 80, NOW() - INTERVAL '5 days', NOW()),
(7, 1, 34, 4, 10, 20, NOW() - INTERVAL '35 days', NOW()),
(8, 1, 28, 3, 8, 15, NOW() - INTERVAL '40 days', NOW()),
(9, 2, 67, 7, 15, 30, NOW() - INTERVAL '45 days', NOW()),
(10, 2, 54, 6, 12, 25, NOW() - INTERVAL '50 days', NOW());

-- Add inventory for remaining products (11-50)
INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, reorder_point, reorder_quantity, last_restock_date, updated_at)
SELECT 
    id,
    warehouse_id,
    stock_quantity,
    FLOOR(stock_quantity * 0.1),
    FLOOR(stock_quantity * 0.2),
    FLOOR(stock_quantity * 0.5),
    NOW() - (INTERVAL '1 day' * FLOOR(RANDOM() * 60)),
    NOW()
FROM products
WHERE id BETWEEN 11 AND 50;

-- ============================================================================
-- CARRIERS
-- ============================================================================

INSERT INTO carriers (id, name, code, tracking_url_template, is_active, base_rate, per_kg_rate, estimated_delivery_days, created_at) VALUES
(1, 'FedEx Express', 'FEDEX', 'https://www.fedex.com/fedextrack/?tracknumbers={tracking_number}', true, 8.99, 2.50, 2, NOW() - INTERVAL '365 days'),
(2, 'UPS Ground', 'UPS', 'https://www.ups.com/track?tracknum={tracking_number}', true, 7.99, 2.00, 5, NOW() - INTERVAL '365 days'),
(3, 'USPS Priority Mail', 'USPS', 'https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}', true, 6.99, 1.50, 3, NOW() - INTERVAL '365 days'),
(4, 'DHL Express', 'DHL', 'https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}', true, 12.99, 3.50, 1, NOW() - INTERVAL '300 days'),
(5, 'Amazon Logistics', 'AMZL', 'https://track.amazon.com/tracking/{tracking_number}', true, 5.99, 1.00, 2, NOW() - INTERVAL '200 days');

SELECT setval('carriers_id_seq', 5);

-- ============================================================================
-- SUMMARY
-- ============================================================================

-- Display summary of inserted data
DO $$
DECLARE
    user_count INTEGER;
    customer_count INTEGER;
    warehouse_count INTEGER;
    supplier_count INTEGER;
    product_count INTEGER;
    carrier_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO customer_count FROM customers;
    SELECT COUNT(*) INTO warehouse_count FROM warehouses;
    SELECT COUNT(*) INTO supplier_count FROM suppliers;
    SELECT COUNT(*) INTO product_count FROM products;
    SELECT COUNT(*) INTO carrier_count FROM carriers;
    
    RAISE NOTICE '============================================';
    RAISE NOTICE 'SEED DATA PART 1 - CORE DATA COMPLETED';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Users created: %', user_count;
    RAISE NOTICE 'Customers created: %', customer_count;
    RAISE NOTICE 'Warehouses created: %', warehouse_count;
    RAISE NOTICE 'Suppliers created: %', supplier_count;
    RAISE NOTICE 'Products created: %', product_count;
    RAISE NOTICE 'Carriers created: %', carrier_count;
    RAISE NOTICE '============================================';
END $$;
