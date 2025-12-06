"""
API Server - Main application entry point

This is a sample microservice for testing KGroot RCA integration.
Contains intentional bugs for testing purposes.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Server", version="1.0.0")

# Simulated database
orders_db = {}
users_db = {}


class Order(BaseModel):
    order_id: str
    user_id: str
    items: List[dict]
    total: float


class User(BaseModel):
    user_id: str
    name: str
    email: str


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
def readiness_check():
    """Readiness check - verifies dependencies"""
    # BUG: Missing DATABASE_URL check causes crash when DB is unavailable
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # This should return unhealthy, not crash
        raise Exception("DATABASE_URL not configured")
    return {"status": "ready", "database": "connected"}


@app.post("/orders")
def create_order(order: Order):
    """Create a new order"""
    # BUG: No validation on order total - can be negative
    orders_db[order.order_id] = order.dict()
    logger.info(f"Created order {order.order_id}")
    return {"status": "created", "order_id": order.order_id}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    """Get order by ID"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]


@app.get("/orders/user/{user_id}")
def get_user_orders(user_id: str):
    """Get all orders for a user"""
    # BUG: Memory leak - loads all orders into memory for filtering
    all_orders = list(orders_db.values())
    user_orders = [o for o in all_orders if o["user_id"] == user_id]
    return {"orders": user_orders, "count": len(user_orders)}


def calculate_total(items: List[dict]) -> float:
    """Calculate order total from items

    BUG: TypeError when item has no 'price' field
    This causes CrashLoopBackOff when processing malformed orders
    """
    total = 0
    for item in items:
        # BUG: Missing null check - crashes if price is None
        total += item["price"] * item["quantity"]
    return total


@app.post("/orders/calculate")
def calculate_order_total(items: List[dict]):
    """Calculate total for items"""
    try:
        total = calculate_total(items)
        return {"total": total}
    except KeyError as e:
        # BUG: Exposes internal error details
        raise HTTPException(status_code=500, detail=f"Missing field: {e}")
    except TypeError as e:
        raise HTTPException(status_code=500, detail=f"Type error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
