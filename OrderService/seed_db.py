import os
import psycopg2
import csv

# Read database config from .env or environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "order_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")

SEED_PATH = os.getenv("SEED_PATH", "./Seed Data")  # path to CSVs

def seed_db():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()

    # Truncate tables
    cur.execute("TRUNCATE TABLE ordersapp_orderitem CASCADE;")
    cur.execute("TRUNCATE TABLE ordersapp_order CASCADE;")
    print("Tables truncated")

    # Load orders
    with open(os.path.join(SEED_PATH, "eci_orders.csv"), "r") as f:
        cur.copy_expert(
            "COPY ordersapp_order(order_id, customer_id, order_status, payment_status, order_total, created_at) FROM STDIN WITH CSV HEADER",
            f,
        )
    print("Orders loaded")

    # Load order items
    with open(os.path.join(SEED_PATH, "eci_order_items.csv"), "r") as f:
        cur.copy_expert(
            "COPY ordersapp_orderitem(order_item_id, order_id, product_id, sku, quantity, unit_price) FROM STDIN WITH CSV HEADER",
            f,
        )
    print("Order items loaded")

    conn.commit()
    cur.close()
    conn.close()
    print("Seeding completed!")

if __name__ == "__main__":
    seed_db()
