import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

@app.on_event("startup")
def startup():
    logger.info("Starting up order-api — connecting to database")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            item TEXT NOT NULL,
            quantity INT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    cur.close()
    logger.info("Database ready — orders table verified")

@app.get("/orders")
def list_orders():
    logger.info("Fetching all orders")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, item, quantity, status FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    logger.info(f"Returning {len(rows)} orders")
    return [{"id": r[0], "item": r[1], "quantity": r[2], "status": r[3]} for r in rows]

@app.post("/orders")
def create_order(payload: dict):
    logger.info(f"Creating order: item={payload.get('item')} quantity={payload.get('quantity')}")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (item, quantity) VALUES (%s, %s) RETURNING id",
        (payload["item"], payload["quantity"])
    )
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Order created successfully: id={order_id} item={payload['item']}")
    return {"id": order_id, "item": payload["item"], "quantity": payload["quantity"], "status": "pending"}

@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "ok"}