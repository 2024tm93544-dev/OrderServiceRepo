from django.db import models
from django.utils import timezone
from decimal import Decimal
from .Status.order_status import OrderStatus
from .Status.payment_status import PaymentStatus


class Order(models.Model):
    ORDER_STATUS_CHOICES = [(s.value, s.name.title()) for s in OrderStatus]
    PAYMENT_STATUS_CHOICES = [(s.value, s.name.title()) for s in PaymentStatus]

    order_id = models.BigAutoField(primary_key=True)
    customer_id = models.BigIntegerField()
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    order_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ordersapp_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - Customer {self.customer_id}"


class OrderItem(models.Model):
    order_item_id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.BigIntegerField()
    sku = models.CharField(max_length=100)
    warehouse = "WH1"
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'ordersapp_orderitem'

    def __str__(self):
        return f"Item {self.order_item_id} (Order {self.order.order_id})"
