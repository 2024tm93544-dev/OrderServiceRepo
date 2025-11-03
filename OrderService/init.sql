-- init.sql : Seed sample data for OrderService
-- It creates app tables used in your SQL injection below (ordersapp_order, ordersapp_orderitem)

CREATE TABLE IF NOT EXISTS ordersapp_order (
  order_id SERIAL PRIMARY KEY,
  customer_id INT,
  order_status VARCHAR(50),
  payment_status VARCHAR(50),
  order_total NUMERIC DEFAULT 0,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ordersapp_orderitem (
  orderitem_id SERIAL PRIMARY KEY,
  product_id INT,
  sku VARCHAR(128),
  quantity INT,
  unit_price NUMERIC(10,2),
  order_id INT REFERENCES ordersapp_order(order_id) ON DELETE CASCADE
);

-- Remove existing rows safely
DELETE FROM ordersapp_orderitem;
DELETE FROM ordersapp_order;

-- Insert sample orders (15 customers, 20 orders)
INSERT INTO ordersapp_order (customer_id, order_status, payment_status, order_total, created_at)
VALUES
(1, 'Pending', 'Pending', 0, NOW() - INTERVAL '1 day'),
(1, 'Completed', 'Paid', 0, NOW() - INTERVAL '2 day'),
(2, 'Shipped', 'Paid', 0, NOW() - INTERVAL '3 day'),
(3, 'Pending', 'Pending', 0, NOW() - INTERVAL '4 day'),
(3, 'Cancelled', 'Refunded', 0, NOW() - INTERVAL '5 day'),
(4, 'Completed', 'Paid', 0, NOW() - INTERVAL '6 day'),
(4, 'Pending', 'Pending', 0, NOW() - INTERVAL '7 day'),
(5, 'Completed', 'Paid', 0, NOW() - INTERVAL '8 day'),
(5, 'Processing', 'Pending', 0, NOW() - INTERVAL '9 day'),
(6, 'Shipped', 'Paid', 0, NOW() - INTERVAL '10 day'),
(7, 'Pending', 'Pending', 0, NOW() - INTERVAL '11 day'),
(8, 'Completed', 'Paid', 0, NOW() - INTERVAL '12 day'),
(9, 'Cancelled', 'Refunded', 0, NOW() - INTERVAL '13 day'),
(10, 'Completed', 'Paid', 0, NOW() - INTERVAL '14 day'),
(10, 'Processing', 'Pending', 0, NOW() - INTERVAL '15 day'),
(11, 'Pending', 'Pending', 0, NOW() - INTERVAL '16 day'),
(12, 'Completed', 'Paid', 0, NOW() - INTERVAL '17 day'),
(13, 'Shipped', 'Paid', 0, NOW() - INTERVAL '18 day'),
(14, 'Completed', 'Paid', 0, NOW() - INTERVAL '19 day'),
(15, 'Pending', 'Pending', 0, NOW() - INTERVAL '20 day');

-- Insert random order items (3 per order)
INSERT INTO ordersapp_orderitem (product_id, sku, quantity, unit_price, order_id)
SELECT
    (RANDOM() * 100)::INT + 1 AS product_id,
    CONCAT('SKU_', (RANDOM() * 1000)::INT) AS sku,
    (RANDOM() * 5)::INT + 1 AS quantity,
    ROUND((RANDOM() * 90 + 10)::NUMERIC, 2) AS unit_price,
    o.order_id
FROM ordersapp_order o
CROSS JOIN generate_series(1, 3);

-- Recompute totals
UPDATE ordersapp_order o
SET order_total = sub.total
FROM (
    SELECT order_id, SUM(quantity * unit_price) AS total
    FROM ordersapp_orderitem
    GROUP BY order_id
) AS sub
WHERE o.order_id = sub.order_id;
