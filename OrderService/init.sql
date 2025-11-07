-- Truncate tables
TRUNCATE TABLE ordersapp_orderitem CASCADE;
TRUNCATE TABLE ordersapp_order CASCADE;

-- Load Orders
COPY ordersapp_order(order_id, customer_id, order_status, payment_status, order_total, created_at) 
FROM '/app/seed_data/eci_orders.csv' DELIMITER ',' CSV HEADER;

-- Load Order Items
COPY ordersapp_orderitem(order_item_id, order_id, product_id, sku, quantity, unit_price) 
FROM '/app/seed_data/eci_order_items.csv' DELIMITER ',' CSV HEADER;
