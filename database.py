import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "stocksense.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS sales (
            date TEXT, product_id TEXT, units_sold INTEGER, revenue REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS inventory (
            product_id TEXT PRIMARY KEY, on_hand INTEGER, last_restock_date TEXT,
            inventory_value REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY, product_name TEXT, category TEXT, supplier TEXT,
            selling_price REAL, unit_cost REAL, reorder_point INTEGER, lead_time_days INTEGER)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS suppliers (
            supplier TEXT PRIMARY KEY, avg_lead_time_days INTEGER, on_time_rate REAL, contact TEXT)""")
        conn.commit()

def save_frame(table, frame, if_exists="replace"):
    with get_connection() as conn:
        frame.to_sql(table, conn, if_exists=if_exists, index=False)

def read_table(table):
    with get_connection() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def seed_if_empty(data_dir):
    init_db()
    if len(read_table("products")) == 0:
        for table in ["products", "sales", "inventory", "suppliers"]:
            path = Path(data_dir) / f"{table}.csv"
            if path.exists():
                save_frame(table, pd.read_csv(path))
