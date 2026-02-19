import random
import string

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from orders.models import Customer, Order, OrderItem

def _rand_email(i: int) -> str:
    return f"user{i}@example.com"

def _rand_name() -> str:
    return "User " + "".join(random.choices(string.ascii_uppercase, k=5))

class DevSeedView(APIView):
    # ... docstring ...

    def post(self, request):
        customers = int(request.data.get("customers", 100))
        orders_per_customer = int(request.data.get("orders_per_customer", 5))
        items_per_order = int(request.data.get("items_per_order", 3))

        created_customers = 0
        created_orders = 0
        created_items = 0

        last_id = Customer.objects.order_by('-id').values_list('id', flat=True).first() or 0
        start_idx = int(last_id) + 1

        with transaction.atomic():
            for i in range(start_idx, start_idx + customers):
                c = Customer.objects.create(
                    name=_rand_name(),
                    email=_rand_email(i),
                    is_active=True,
                )
                created_customers += 1

                for _ in range(orders_per_customer):
                    status_choice = random.choices(
                        [Order.Status.PAID, Order.Status.DRAFT, Order.Status.SHIPPED],
                        weights=[0.55, 0.35, 0.10],
                    )[0]
                    # Don't set total yet
                    o = Order.objects.create(customer=c, status=status_choice)
                    created_orders += 1

                    items_objs = []
                    order_total = 0
                    for j in range(items_per_order):
                        sku = f"SKU-{random.randint(1, 200)}"
                        qty = random.randint(1, 5)
                        price = random.choice([199, 499, 999, 1499, 2499])
                        
                        items_objs.append(OrderItem(order=o, sku=sku, quantity=qty, unit_price_cents=price))
                        order_total += (qty * price)
                        created_items += 1
                    
                    OrderItem.objects.bulk_create(items_objs)
                    
                    if order_total > 0:
                        o.total_cents = order_total
                        o.save(update_fields=["total_cents"])

        return Response({
            "customers": created_customers,
            "orders": created_orders,
            "items": created_items,
        }, status=status.HTTP_201_CREATED)
