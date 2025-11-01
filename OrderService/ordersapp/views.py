from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from urllib.parse import urlencode

from .models import Order
from .serialzer import OrderSerializer
from .Services.order_services import OrderService
from .Services.inventory_client import reserve_inventory, release_inventory
from .Status.order_status import OrderStatus, SortBy, Direction
from .Status.payment_status import PaymentStatus
from .Status.shipping_status import ShippingStatus
from .Services.payment_client import charge_payment
from .Services.shipping_client import get_shipping_queryset_for_customer, create_shipment
from .decorator import authorized_user
from rest_framework.permissions import AllowAny


class OrderViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # --- Create new order ---
    @swagger_auto_schema(
        operation_summary="Create a new order",
        operation_description="Creates an order, reserves inventory, charges payment, and updates status.",
        request_body=OrderSerializer,
        responses={201: OrderSerializer, 400: "Inventory reservation or payment failed"}
    )
    @action(detail=False, methods=['post'], url_path='create')
    @authorized_user 
    def create_order(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data['items']
        total = OrderService.calculate_order_total(items)
        serializer.validated_data['order_total'] = total
        order = serializer.save()

        # Reserve inventory
        if not reserve_inventory(order.order_id, items):
            order.order_status = OrderStatus.CANCELLED.value
            order.save()
            return Response({"error": "Inventory reservation failed"}, status=status.HTTP_400_BAD_REQUEST)

        # Charge payment
        if not charge_payment(order.order_id, order.customer_id, total):
            order.order_status = OrderStatus.CANCELLED.value
            order.save()
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

        # Confirm order and create shipment
        order.order_status = OrderStatus.CONFIRMED.value
        order.payment_status = PaymentStatus.PAID.value
        order.save()
        create_shipment(order.order_id, order.customer_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    # --- Cancel order ---
    @swagger_auto_schema(
        operation_summary="Cancel an order",
        operation_description="Cancels an existing order if it is not already completed or cancelled.",
        responses={200: "Order cancelled successfully", 400: "Order cannot be cancelled"}
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    @authorized_user
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.order_status in [OrderStatus.CANCELLED.value, OrderStatus.DELIVERED.value]:
            return Response({"error": "Order cannot be cancelled"}, status=status.HTTP_400_BAD_REQUEST)

        release_inventory(order.order_id, order.items.all())
        order.order_status = OrderStatus.CANCELLED.value
        order.payment_status = PaymentStatus.REFUNDED.value
        order.save()
        return Response({"status": "Order cancelled"}, status=status.HTTP_200_OK)


# --- Get Order Details ---
@swagger_auto_schema(
    method='get',
    operation_summary="Get Order Details",
    operation_description="Fetch detailed information for a specific order by its ID.",
    responses={200: "Order details retrieved", 404: "Order not found"}
)
@api_view(['GET'])
@authorized_user
def get_order_details(request, pk=None):
    order_data = OrderService.get_order_data(pk)
    if not order_data:
        return Response({"error": "Order not found"}, status=404)
    return Response(order_data)


# --- View Order History ---
@swagger_auto_schema(
    method='get',
    operation_summary="Get Order History",
    operation_description="Fetch order history for a customer with search, filter, and sorting options.",
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description="Search orders", type=openapi.TYPE_STRING),
        openapi.Parameter('status_filter', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[s.value for s in OrderStatus]),
        openapi.Parameter('payment_filter', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[s.value for s in PaymentStatus]),
        openapi.Parameter('shipping_filter', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[s.value for s in ShippingStatus]),
        openapi.Parameter('sort_by', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[s.value for s in SortBy]),
        openapi.Parameter('sort_dir', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=[s.value for s in Direction]),
    ],
    responses={200: "Orders retrieved successfully"}
)
@api_view(['GET'])
@authorized_user
def order_history(request, customer_id):
    # Extract filters
    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status_filter", "").strip()
    payment_filter = request.GET.get("payment_filter", "").strip()
    shipping_filter = request.GET.get("shipping_filter", "").strip()
    sort_by = request.GET.get("sort_by", "").strip()
    sort_dir = request.GET.get("sort_dir", "").strip()

    # Query customer orders
    orders_qs = Order.objects.filter(customer_id=customer_id).prefetch_related("items")

    # Apply filters
    if search:
        orders_qs = orders_qs.filter(
            Q(order_id__icontains=search)
            | Q(order_status__icontains=search)
            | Q(payment_status__icontains=search)
            | Q(items__sku__icontains=search)
        ).distinct()
    if status_filter:
        orders_qs = orders_qs.filter(order_status=status_filter)
    if payment_filter:
        orders_qs = orders_qs.filter(payment_status=payment_filter)

    # Fetch and merge shipping info
    shipping_qs = get_shipping_queryset_for_customer(list(orders_qs))
    shipping_map = {s["order_id"]: s for s in shipping_qs}
    orders_with_shipping = []
    for order in orders_qs:
        ship_info = shipping_map.get(order.order_id, {"shipping_status": "Unknown"})
        if not shipping_filter or ship_info["shipping_status"].lower() == shipping_filter.lower():
            items_data = [{"sku": i.sku, "quantity": i.quantity, "unit_price": i.unit_price} for i in order.items.all()]
            order.total_calculated = OrderService.calculate_order_total(items_data)
            order.shipping_status = ship_info["shipping_status"]
            orders_with_shipping.append(order)

    # Apply sorting
    reverse = sort_dir == Direction.DESC.value
    if sort_by == SortBy.DATE.value:
        orders_with_shipping.sort(key=lambda o: o.created_at, reverse=reverse)
    elif sort_by == SortBy.CREATED_AT.value:
        orders_with_shipping.sort(key=lambda o: o.total_calculated, reverse=reverse)

    # Paginate
    paginator = Paginator(orders_with_shipping, 3)
    orders_page = paginator.get_page(request.GET.get("page"))

    # Dropdown options
    context = {
        "orders": orders_page,
        "shipping_qs": shipping_qs,
        "search": search,
        "status_filter": status_filter,
        "payment_filter": payment_filter,
        "shipping_filter": shipping_filter,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "all_order_statuses": [s.value for s in OrderStatus],
        "all_payment_statuses": [s.value for s in PaymentStatus],
        "all_shipping_statuses": [s.value for s in ShippingStatus],
        "all_sort_by_options": [s.value for s in SortBy],
        "all_sort_directions": [d.value for d in Direction],
        "request_path": request.path,
        "query_without_page": urlencode({k: v for k, v in request.GET.items() if k != "page" and v}),
    }

    redirect_url = OrderService.get_clean_redirect_url(request)
    if redirect_url:
        return redirect(redirect_url)

    return render(request, "ordersapp/order_history.html", context)
