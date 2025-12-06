"""
Payment Service - Handles payment processing

Contains intentional bugs for testing KGroot RCA:
- Memory leak causing OOMKilled
- Connection pool exhaustion
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service", version="1.0.0")

# BUG: Unbounded cache causes OOMKilled
payment_cache = {}


class PaymentRequest(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    currency: str = "USD"


class PaymentResult(BaseModel):
    payment_id: str
    status: str
    transaction_id: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "cache_size": len(payment_cache)}


@app.post("/payments/process")
def process_payment(payment: PaymentRequest):
    """Process a payment

    BUG: Memory leak - payments cached forever without eviction
    This causes OOMKilled after processing many payments
    """
    # Simulate payment processing
    time.sleep(0.1)

    # BUG: Cache grows unbounded - no TTL or size limit
    payment_cache[payment.payment_id] = {
        "payment": payment.dict(),
        "processed_at": time.time(),
        # BUG: Storing large payload unnecessarily
        "debug_data": "x" * 10000  # 10KB per payment
    }

    logger.info(f"Processed payment {payment.payment_id}, cache size: {len(payment_cache)}")

    return PaymentResult(
        payment_id=payment.payment_id,
        status="completed",
        transaction_id=f"txn_{payment.payment_id}"
    )


@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):
    """Get payment status"""
    if payment_id not in payment_cache:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment_cache[payment_id]["payment"]


@app.post("/payments/refund/{payment_id}")
def refund_payment(payment_id: str):
    """Refund a payment

    BUG: No idempotency check - can refund same payment multiple times
    """
    if payment_id not in payment_cache:
        raise HTTPException(status_code=404, detail="Payment not found")

    # BUG: Should check if already refunded
    payment_cache[payment_id]["status"] = "refunded"
    logger.info(f"Refunded payment {payment_id}")

    return {"status": "refunded", "payment_id": payment_id}


def load_payment_history():
    """Load payment history on startup

    BUG: Loads entire history into memory
    With large history, this causes OOMKilled on pod startup
    """
    # Simulate loading large history
    logger.info("Loading payment history...")
    history = []
    for i in range(100000):  # 100k records
        history.append({
            "id": f"payment_{i}",
            "data": "x" * 1000  # 1KB each = 100MB total
        })
    return history


if __name__ == "__main__":
    import uvicorn
    # BUG: Loading history on startup causes memory spike
    # history = load_payment_history()
    uvicorn.run(app, host="0.0.0.0", port=8081)
