from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from urllib.parse import urlencode
from django.http import JsonResponse
from django.db import connection
from rest_framework.permissions import AllowAny

# --- Import project modules ---
from .models import Order
from .serializer import OrderSerializer
from .Services.order_services import OrderService
from .Services.inventory_client import reserve_inventory, release_inventory
from .Services.payment_client import charge_payment
from .Services.shipping_client import get_shipping_queryset_for_customer, create_shipment
from .Status.order_status import OrderStatus, SortBy, Direction
from .Status.payment_status import PaymentStatus
from .Status.shipping_status import ShippingStatus
from .Services.notification_client import send_notification


# --- ViewSet for managing Orders (CRUD operations) ---
class OrderViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    # -------------------------------------------------------------
    # LIST ORDERS
    # -------------------------------------------------------------
    @swagger_auto_schema(
        operation_summary="List all orders",
        operation_description="Retrieve all existing orders (JWT required).",
        responses={200: OrderSerializer(many=True)}
    )
    def list(self, request):
        """List all orders."""
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    # -------------------------------------------------------------
    # CREATE ORDER
    # -------------------------------------------------------------
    @swagger_auto_schema(
        operation_summary="Create a new order",
        operation_description="Creates an order, reserves inventory, charges payment, and updates status.",
        request_body=OrderSerializer,
        responses={201: OrderSerializer, 400: "Inventory reservation or payment failed"}
    )
    @action(detail=False, methods=['post'], url_path='create')
    def create_order(self, request):
        """Create a new order with inventory, payment, and shipment flow."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.get('items', [])
        total = OrderService.calculate_order_total(items) if items else 0
        serializer.validated_data['order_total'] = total

        order = serializer.save()
        # Handle empty item list
        if not items:
            return Response(
        {"error": "Cannot create an order without items."},
        status=status.HTTP_400_BAD_REQUEST
    )

        # Reserve inventory first
        if not reserve_inventory(order.order_id, items):
            order.order_status = OrderStatus.CANCELLED.value
            order.save()
            return Response({"error": "Inventory reservation failed"}, status=status.HTTP_400_BAD_REQUEST)

        # Charge payment
        if not charge_payment(order.order_id, order.customer_id, total):
            release_inventory(order.order_id, items)
            order.order_status = OrderStatus.CANCELLED.value
            order.payment_status = PaymentStatus.FAILED.value
            order.save()
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

        # Create shipment on success
        create_shipment(order.order_id, order.customer_id)
        order.order_status = OrderStatus.CONFIRMED.value
        order.payment_status = PaymentStatus.PAID.value
        order.save()
        send_notification("ORDER_CREATED", {
          "order_id": order.order_id,
          "order_total": str(order.order_total)
        })
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------------
    # UPDATE ORDER
    # -------------------------------------------------------------
    @swagger_auto_schema(
        operation_summary="Update order status (payment/shipping/order)",
        operation_description=(
            "Updates only the order, payment, or shipping status of an existing order. "
            "Cannot update delivered or cancelled orders. "
            "Accepts partial updates for status transitions only."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_status': openapi.Schema(type=openapi.TYPE_STRING, enum=[s.value for s in OrderStatus]),
                'payment_status': openapi.Schema(type=openapi.TYPE_STRING, enum=[s.value for s in PaymentStatus]),
                'shipping_status': openapi.Schema(type=openapi.TYPE_STRING, enum=[s.value for s in ShippingStatus]),
            },
            required=[],
        ),
        responses={
            200: OrderSerializer,
            400: "Invalid transition or not allowed to update."
        }
    )
    @action(detail=True, methods=['patch'], url_path='update')
    def update_order(self, request, pk=None):
        """
        Update order status safely (Order/Payment/Shipping).
        Does not change items or trigger external service actions.
        """
        order = self.get_object()

        # 🔒 Block final state updates
        if order.order_status in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
            return Response(
                {"error": "Cannot update a delivered or cancelled order."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_order_status = request.data.get('order_status')
        new_payment_status = request.data.get('payment_status')
        new_shipping_status = request.data.get('shipping_status')

        # 🧩 Validate payment status transitions
        if new_payment_status:
            if order.payment_status == PaymentStatus.FAILED.value and new_payment_status == PaymentStatus.PAID.value:
                return Response(
                    {"error": "Cannot change payment from FAILED to PAID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.payment_status = new_payment_status

        # 🚚 Validate order status transitions
        if new_order_status:
            valid_transitions = {
                OrderStatus.PENDING.value: [OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value],
                OrderStatus.CONFIRMED.value: [OrderStatus.SHIPPED.value, OrderStatus.CANCELLED.value],
                OrderStatus.SHIPPED.value: [OrderStatus.DELIVERED.value],
            }

            current = order.order_status
            if new_order_status not in valid_transitions.get(current, []):
                return Response(
                    {"error": f"Invalid transition from {current} to {new_order_status}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.order_status = new_order_status

        # 🧾 Shipping status tracking
        if new_shipping_status:
            order.shipping_status = new_shipping_status

        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    # -------------------------------------------------------------
    # CANCEL ORDER
    # -------------------------------------------------------------
    @swagger_auto_schema(
        operation_summary="Cancel an order",
        operation_description="Cancels an existing order if it is not already completed or cancelled.",
        responses={200: "Order cancelled successfully", 400: "Order cannot be cancelled"}
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        """Cancel order, release inventory, and refund payment."""
        order = self.get_object()
        if order.order_status in [OrderStatus.CANCELLED.value, OrderStatus.DELIVERED.value]:
            return Response({"error": "Order cannot be cancelled"}, status=status.HTTP_400_BAD_REQUEST)

        # Release reserved inventory
        release_inventory(order.order_id, order.items.all())

        # Update order status
        order.order_status = OrderStatus.CANCELLED.value
        order.payment_status = PaymentStatus.REFUNDED.value
        order.save()
        return Response({"status": "Order cancelled successfully"}, status=status.HTTP_200_OK)


# -----------------------------------------------------------------
# GET ORDER DETAILS
# -----------------------------------------------------------------
@swagger_auto_schema(
    method='get',
    operation_summary="Get Order Details",
    operation_description="Fetch detailed information for a specific order by its ID.",
    responses={200: "Order details retrieved", 404: "Order not found"}
)
@api_view(['GET'])
def get_order_details(request, pk=None):
    """Get order details by order ID."""
    order_data = OrderService.get_order_data(pk)
    if not order_data:
        return Response({"error": "Order not found"}, status=404)
    return Response(order_data)


# -----------------------------------------------------------------
# ORDER HISTORY (For UI view + pagination)
# -----------------------------------------------------------------
@swagger_auto_schema(auto_schema=None)
def order_history(request, customer_id):
    """Display customer order history with filters and pagination."""
    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status_filter", "").strip()
    payment_filter = request.GET.get("payment_filter", "").strip()
    shipping_filter = request.GET.get("shipping_filter", "").strip()
    sort_by = request.GET.get("sort_by", "").strip()
    sort_dir = request.GET.get("sort_dir", "").strip()

    # Base queryset
    orders_qs = Order.objects.filter(customer_id=customer_id).prefetch_related("items")

    # Search filter
    if search:
        orders_qs = orders_qs.filter(
            Q(order_id__icontains=search)
            | Q(order_status__icontains=search)
            | Q(payment_status__icontains=search)
            | Q(items__sku__icontains=search)
        ).distinct()

    # Status and payment filters
    if status_filter:
        orders_qs = orders_qs.filter(order_status__iexact=status_filter)
    if payment_filter:
        orders_qs = orders_qs.filter(payment_status__iexact=payment_filter)

    # Fetch shipping info
    shipping_qs = get_shipping_queryset_for_customer(list(orders_qs))
    shipping_map = {s["order_id"]: s for s in shipping_qs}


    for order in orders_qs:
        order.calculated_total = OrderService.calculate_order_total(order)


    # Merge orders + shipping
    orders_with_shipping = []
    for order in orders_qs:
        ship_info = shipping_map.get(order.order_id, {"shipping_status": "Unknown"})
        ship_status = ship_info.get("shipping_status", "Unknown")
        if not shipping_filter or ship_status.lower() == shipping_filter.lower():
            order.shipping_status = ship_status
            orders_with_shipping.append(order)

    # Sorting logic
    reverse = sort_dir == Direction.DESC.value
    if sort_by == SortBy.DATE.value:
        orders_with_shipping.sort(key=lambda o: o.created_at, reverse=reverse)
    elif sort_by == SortBy.CREATED_AT.value:
        orders_with_shipping.sort(key=lambda o: o.order_total, reverse=reverse)
    else:
        orders_with_shipping.sort(key=lambda o: o.created_at, reverse=True)

    # Pagination
    paginator = Paginator(orders_with_shipping, 3)
    orders_page = paginator.get_page(request.GET.get("page"))

    # Context for rendering template
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


# -----------------------------------------------------------------
# HEALTH CHECK (for Docker/Kubernetes readiness probe)
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint to verify DB connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        return JsonResponse({"status": "healthy"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)


# -----------------------------------------------------------------
# ROOT VIEW
# -----------------------------------------------------------------
def root_view(request):
    """Root endpoint to verify service availability."""
    return JsonResponse({"message": "Order Service running"}, status=200)
