import requests
from django.conf import settings

NOTIFICATION_URL = getattr(settings, "NOTIFICATION_SERVICE_URL", "http://notification-service:5000/v1/notifications")

def send_notification(event_type, data):
    try:
        r = requests.post(NOTIFICATION_URL, json={"type": event_type, "data": data}, timeout=5)
        print(f"[NotificationClient] Sent {event_type}: {r.status_code}")
    except Exception as e:
        print(f"[NotificationClient] Failed to send {event_type}: {e}")

