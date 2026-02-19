from django.db.models import Q, Count, Sum
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Order, OrderItem
from .serializers import CustomerSerializer, OrderSerializer, OrderItemSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Default behavior: hide archived orders in list views.
        # (Note: detail views should still retrieve by id.)
        if self.action == "list":
            qs = qs.filter(is_archived=False)
            
            status_param = self.request.query_params.get("status")
            if status_param:
                qs = qs.filter(status=status_param)

            email_param = self.request.query_params.get("email")
            if email_param:
                qs = qs.filter(customer__email__icontains=email_param)
        return qs

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response({"id": order.id, "status": order.status})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        order = self.get_object()
        order.is_archived = True
        order.save(update_fields=["is_archived", "updated_at"])
        return Response({"id": order.id, "is_archived": order.is_archived})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-id")
    serializer_class = OrderItemSerializer

class OrdersSummaryView(APIView):
    """Intentionally slow summary endpoint.

    Returns top customers by total spent (paid orders only).
    This is written in a purposely inefficient way to give candidates a perf target.
    """

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))

        # Optimized query using aggregation
        
        customers = (Customer.objects.filter(is_active=True)
                     .annotate(
                         paid_order_count=Count('orders', filter=Q(orders__status=Order.Status.PAID, orders__is_archived=False)),
                         total_spent=Coalesce(Sum('orders__total_cents', filter=Q(orders__status=Order.Status.PAID, orders__is_archived=False)), 0)
                     )
                     .order_by("-total_spent")[:limit])

        rows = []
        for c in customers:
            rows.append({
                "customer_id": c.id,
                "email": c.email,
                "order_count": c.paid_order_count,
                "total_cents": c.total_spent, # Coalesce guarantees 0 instead of None
            })

        return Response({"limit": limit, "rows": rows})
