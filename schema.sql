DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vendor_name TEXT NOT NULL,
  pickup_address TEXT NOT NULL,
  delivery_address TEXT NOT NULL,
  delivery_type TEXT NOT NULL,
  is_quick INTEGER NOT NULL,
  status TEXT NOT NULL,
  driver_id INTEGER,
  delivery_time TEXT
);

-- Insert sample data WITHOUT any fee columns
-- Group 1: Laxmi Nagar, Lane 2
INSERT INTO orders (vendor_name, pickup_address, delivery_address, delivery_type, is_quick, status, driver_id) VALUES
('Ramesh Chaat', 'Wholesale Mandi, Stall 14', 'Laxmi Nagar, Lane 2', 'door', 1, 'available', NULL),
('Juice Center', 'Fruit Market, Gate 3', 'Laxmi Nagar, Lane 2', 'common', 0, 'available', NULL),
('Samosa Corner', 'Wholesale Mandi, Stall 8', 'Laxmi Nagar, Lane 2', 'door', 0, 'available', NULL);

-- Group 2: Nehru Place, Main Square
INSERT INTO orders (vendor_name, pickup_address, delivery_address, delivery_type, is_quick, status, driver_id) VALUES
('Flower Shop', 'Flower Market, Section A', 'Nehru Place, Main Square', 'door', 1, 'available', NULL),
('Tech Repair', 'Gaffar Market', 'Nehru Place, Main Square', 'common', 0, 'available', NULL);