from ..models import Order
from decimal import Decimal, ROUND_HALF_EVEN
from urllib.parse import urlencode


class OrderService:
    SHIPPING_COST = Decimal('50.00')  # fixed shipping
    TAX_PERCENT = Decimal('0.05')     # 5% tax

    @staticmethod
    def calculate_order_total(order):
        """
        Calculate order total from items in DB + 5% tax + $50 shipping.
        """
        items = order
        subtotal = sum(i["unit_price"] * i["quantity"] for i in items)

        total = subtotal * (1 + OrderService.TAX_PERCENT) + OrderService.SHIPPING_COST
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    
    @staticmethod
    def get_order_data(order_id):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return None
        return {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "items": [
                {"sku": i.sku, "quantity": i.quantity, "unit_price": i.unit_price}
                for i in order.items.all()
            ],
        }
    
    @staticmethod
    def get_clean_redirect_url(request):
        search = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status_filter', '').strip()
        payment_filter = request.GET.get('payment_filter', '').strip()
        shipping_filter = request.GET.get('shipping_filter', '').strip()
        sort_by = request.GET.get('sort_by', '').strip()
        sort_dir = request.GET.get('sort_dir', '').strip()
        page = request.GET.get('page', '').strip()

        # Keep only non-empty filters
        valid_params = {}
        if search:
            valid_params['search'] = search
        if status_filter:
            valid_params['status_filter'] = status_filter
        if payment_filter:
            valid_params['payment_filter'] = payment_filter
        if shipping_filter:
            valid_params['shipping_filter'] = shipping_filter
        if sort_by:
            valid_params['sort_by'] = sort_by
        if sort_dir:
            valid_params['sort_dir'] = sort_dir
        if page:
            valid_params['page'] = page

        # No params? no redirect
        if not request.GET:
            return None

        clean_query = urlencode(valid_params)
        clean_url = f"{request.path}?{clean_query}" if clean_query else request.path

        # Prevent redirect loop — only redirect if URL differs
        if clean_url != request.get_full_path():
            return clean_url
        return None

