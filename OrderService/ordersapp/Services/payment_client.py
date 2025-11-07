import requests
from django.conf import settings
import random
from ..Status.payment_status import PaymentMethod


# Base URL of the Payment Service
PAYMENT_SERVICE_URL = getattr(settings, "PAYMENT_SERVICE_URL", "http://payment-service:8002/v1/payments")
MOCK_PAYMENT = getattr(settings, "USE_MOCK_PAYMENT", True)


def charge_payment(order_id, customer_id, amount):
    """
    Sends a payment charge request to the Payment Service.
    Returns True if successful, False otherwise.
    """
    if MOCK_PAYMENT:
        print(f"[PaymentClient] Mock mode ON – payment for Order {order_id} always succeeds.")
        return True

    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "amount": float(amount),
        "method": random.choice(list(PaymentMethod)).value
    }

    try:
        response = requests.post(f"{PAYMENT_SERVICE_URL}/charge/", json=payload, timeout=5)
        if response.status_code == 200:
            print(f"[PaymentClient] Payment successful for Order {order_id}")
            return True
        else:
            print(f"[PaymentClient] Payment failed for Order {order_id}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[PaymentClient] Payment request failed for Order {order_id}: {e}")
        return False


def refund_payment(order_id):
    """
    Sends a refund request to the Payment Service.
    Returns True if successful, False otherwise.
    """
    if MOCK_PAYMENT:
        print(f"[PaymentClient] Mock mode ON – refund for Order {order_id} always succeeds.")
        return True

    try:
        response = requests.post(f"{PAYMENT_SERVICE_URL}/{order_id}/refund/", timeout=5)
        if response.status_code == 200:
            print(f"[PaymentClient] Refund successful for Order {order_id}")
            return True
        else:
            print(f"[PaymentClient] Refund failed for Order {order_id}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[PaymentClient] Refund request failed for Order {order_id}: {e}")
        return False
