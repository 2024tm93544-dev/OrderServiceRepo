from rest_framework import serializers
from .models import Order, OrderItem
from .Services.order_services import OrderService

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_id', 'sku', 'quantity', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_calculated = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_id', 'customer_id', 'order_status', 'payment_status', 
                  'created_at', 'items', 'order_total', 'total_calculated']

