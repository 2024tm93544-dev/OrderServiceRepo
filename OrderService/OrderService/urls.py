from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ordersapp.views import (OrderViewSet, order_history, get_order_details, health_check, root_view)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# --- Router Configuration ---
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

# --- Swagger / OpenAPI Configuration ---
schema_view = get_schema_view(
    openapi.Info(
        title="Order Service API",
        default_version='v1',
        description="API documentation for Order Service",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# --- URL Patterns ---
urlpatterns = [
    # Core API Routes
    path('v1/', include(router.urls)),
    path('v1/orders/<int:pk>/details/', get_order_details, name='order-details'),
    path('v1/orders/my-orders/<int:customer_id>/', order_history, name='order-history'),

    # Documentation & Health
    path('orders-doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('health/', health_check, name='health-check'),

    # Prometheus Metrics
    path('', include('django_prometheus.urls')),

    # Root Endpoint
    path('home/', root_view, name='root'),
]
