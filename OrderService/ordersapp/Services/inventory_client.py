import requests
from django.conf import settings
import os

# Inventory service base URL (use env var for flexibility in Docker/K8s)
INVENTORY_SERVICE_URL = getattr(settings, "INVENTORY_SERVICE_URL", "http://inventory:8001/v1/inventory")
MOCK_INVENTORY = getattr(settings, "USE_MOCK_INVENTORY", True)

def reserve_inventory(order_id, items):
    """
    Reserve stock for an order.
    items: list of dicts with 'product_id' and 'quantity'
    Returns True if all items reserved successfully, False otherwise.
    """
    if MOCK_INVENTORY:
        print("[InventoryClient] Mock mode ON – reservation always succeeds.")
        return True
    payload = [
            {"product_id": item["product_id"],"warehouse": "WH1", "quantity": item["quantity"]} 
            for item in items
        ]

    try:
        headers = {"Idempotency-Key": str(order_id)}
        for i in payload:
            response = requests.post(
                f"{INVENTORY_SERVICE_URL}/reserve/",
                json=i,
                headers=headers,
                timeout=5
            )   

            if response.status_code == 200:
                return True
            return False
    except requests.exceptions.RequestException as e:
        print(f"[InventoryClient] Reservation failed: {e}")
        return False


def release_inventory(order_id, items):
    """
    Release reserved stock for an order.
    items: list of OrderItem instances or dicts with 'product_id' and 'quantity'
    """
    if MOCK_INVENTORY:
        print("[InventoryClient] Mock mode ON – release always succeeds.")

        return True
    payload = {
        "order_id": order_id,
        "items": []
    }

    for item in items:
        if isinstance(item, dict):
            payload["items"].append({
                "product_id": item["product_id"],
                "quantity": item["quantity"]
            })
        else:  # assume OrderItem instance
            payload["items"].append({
                "product_id": item.product_id,
                "quantity": item.quantity
            })

    try:
        response = requests.post(f"{INVENTORY_SERVICE_URL}/release/", json=payload, timeout=5)
        if response.status_code != 200:
            print(f"[InventoryClient] Failed to release inventory for order {order_id}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"[InventoryClient] Release failed: {e}")
        return False


