-- Truncate tables first to avoid duplicates
TRUNCATE TABLE ordersapp_orderitem CASCADE;
TRUNCATE TABLE ordersapp_order CASCADE;

-- Load Orders from CSV
COPY ordersapp_order(
    order_id,
    customer_id,
    order_status,
    payment_status,
    order_total,
    created_at
)
FROM 'D:/Scalable Service Assignment/OrderService/Seed Data/eci_orders.csv'
DELIMITER ','
CSV HEADER;

-- Load Order Items from CSV
COPY ordersapp_orderitem(
    order_item_id,
    order_id,
    product_id,
    sku,
    quantity,
    unit_price
)
FROM 'D:/Scalable Service Assignment/OrderService/Seed Data/eci_order_items.csv'
DELIMITER ','
CSV HEADER;
