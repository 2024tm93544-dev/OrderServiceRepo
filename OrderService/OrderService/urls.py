from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ordersapp.views import OrderViewSet, order_history,get_order_details
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions 

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

schema_view = get_schema_view(
    openapi.Info(
        title="Order Service API",
        default_version='v1',
        description="API documentation for Order Service",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

urlpatterns = [
    path('v1/', include(router.urls)),
    path('orders-doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # --- Custom endpoints ---
    path('v1/orders/<int:pk>/details/', get_order_details, name='order-details'),
    path('v1/orders/my-orders/<int:customer_id>/', order_history, name='order-history'),

    path('', include('django_prometheus.urls')),
]
