import random
import requests
from datetime import datetime, timedelta
from django.conf import settings
from ordersapp.Status.shipping_status import ShippingStatus

# Configurable via Django settings
SHIPPING_URL = getattr(settings, "SHIPPING_SERVICE_URL", "http://shipping-service:8003/v1/shipping")
USE_MOCK = getattr(settings, "USE_MOCK_SHIPPING", True)

# Internal cache for mock mode (simulates background progression)
_MOCK_SHIPMENTS = {}


# -------------------- FETCH SHIPPING DATA --------------------
def get_shipping_queryset_for_customer(order_qs):
    """Fetch shipping info for a batch of orders."""
    order_ids = [o.order_id for o in order_qs]
    data_fetcher = _fetch_mock_data if USE_MOCK else _fetch_real_data
    data = data_fetcher(order_ids)
    return [
        {
            "order_id": oid,
            "shipping_status": d.get("status", ShippingStatus.UNKNOWN.value),
            "expected_delivery": d.get("expected_delivery")
        }
        for oid, d in data.items()
    ]


def _fetch_mock_data(order_ids):
    """Generate evolving mock shipping data."""
    today = datetime.now().date()
    mock = {}

    for oid in order_ids:
        # Check if this order already has mock data
        existing = _MOCK_SHIPMENTS.get(oid)
        if existing:
            # Occasionally progress to next stage
            current = existing["status"]
            next_status = _next_stage(current)
            existing["status"] = next_status
            _MOCK_SHIPMENTS[oid] = existing
        else:
            # Initialize a new shipment as Pending
            status = ShippingStatus.PENDING.value
            date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            _MOCK_SHIPMENTS[oid] = {"status": status, "expected_delivery": date}

        mock[oid] = _MOCK_SHIPMENTS[oid]

    return mock


def _fetch_real_data(order_ids):
    """Fetch actual data from Shipping Service."""
    data = {}
    for oid in order_ids:
        try:
            r = requests.get(f"{SHIPPING_URL}/{oid}/status/", timeout=5)
            data[oid] = r.json() if r.status_code == 200 else _default(ShippingStatus.UNKNOWN.value)
        except requests.RequestException:
            data[oid] = _default(ShippingStatus.FAILED.value)
    return data


# -------------------- CREATE & UPDATE --------------------
def create_shipment(order_id, customer_id):
    """POST - Create a new shipment after order confirmation."""
    if USE_MOCK:
        today = datetime.now().date()
        status = ShippingStatus.PENDING.value
        _MOCK_SHIPMENTS[order_id] = {
            "status": status,
            "expected_delivery": (today + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        return {"order_id": order_id, "status": status}

    payload = {"order_id": order_id, "customer_id": customer_id}
    try:
        r = requests.post(f"{SHIPPING_URL}/create/", json=payload, timeout=5)
        if r.status_code == 201:
            return r.json()
        return {"order_id": order_id, "status": ShippingStatus.UNKNOWN.value}
    except requests.RequestException:
        return {"order_id": order_id, "status": ShippingStatus.FAILED.value}


def update_shipment_status(order_id, new_status):
    """PATCH - Update shipment status if needed."""
    if USE_MOCK:
        _MOCK_SHIPMENTS[order_id] = {
            "status": new_status,
            "expected_delivery": (datetime.now().date() + timedelta(days=3)).strftime("%Y-%m-%d")
        }
        return {"order_id": order_id, "status": new_status}

    payload = {"shipping_status": new_status}
    try:
        r = requests.patch(f"{SHIPPING_URL}/{order_id}/status/", json=payload, timeout=5)
        return r.json() if r.status_code == 200 else {"error": "Failed to update"}
    except requests.RequestException:
        return {"error": "Connection error"}


# -------------------- INTERNAL HELPERS --------------------
def _next_stage(current):
    """Simulate progression of shipment stages randomly."""
    transitions = {
        ShippingStatus.PENDING.value: [ShippingStatus.SHIPPED.value, ShippingStatus.FAILED.value],
        ShippingStatus.SHIPPED.value: [ShippingStatus.DELIVERED.value, ShippingStatus.FAILED.value],
        ShippingStatus.DELIVERED.value: [ShippingStatus.DELIVERED.value],
        ShippingStatus.FAILED.value: [ShippingStatus.FAILED.value],
        ShippingStatus.UNKNOWN.value: [ShippingStatus.PENDING.value],
    }
    next_options = transitions.get(current, [ShippingStatus.UNKNOWN.value])
    return random.choice(next_options)


def _default(status):
    return {"status": status, "expected_delivery": None}
