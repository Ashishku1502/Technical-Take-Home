from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.db import connection, reset_queries
import time
from orders.models import Customer, Order, OrderItem

@override_settings(DEBUG=True)
class PerformanceTests(TestCase):
    def test_seed_performance(self):
        client = APIClient()
        start_time = time.time()
        reset_queries()
        data = {"customers": 10, "orders_per_customer": 5, "items_per_order": 3}
        res = client.post("/api/dev/seed/", data, format='json')
        self.assertEqual(res.status_code, 201)
        
        query_count = len(connection.queries)
        print(f"Seed Queries: {query_count}")
        # Default implementation 300+
        self.assertLess(query_count, 300)
            
        print(f"Seed time: {time.time() - start_time:.4f}s")

    def test_summary_performance(self):
        # Setup data
        c_count = 10
        o_count = 5
        i_count = 3
        
        # Use bulk create to set up fast
        customers = [Customer(name=f"C{i}", email=f"c{i}@test.com") for i in range(c_count)]
        Customer.objects.bulk_create(customers)
        
        orders = []
        for c in customers:
             for j in range(o_count):
                 orders.append(Order(customer=c, status=Order.Status.PAID, total_cents=0))
        Order.objects.bulk_create(orders)
        
        items = []
        for o in orders:
            for k in range(i_count):
                items.append(OrderItem(order=o, sku="SKU", quantity=1, unit_price_cents=100))
        OrderItem.objects.bulk_create(items)
        
        # Manually update total_cents since bulk_create skips save
        Order.objects.all().update(total_cents=i_count * 100)

        client = APIClient()
        reset_queries()
        start_time = time.time()
        res = client.get("/api/orders/summary/?limit=50")
        self.assertEqual(res.status_code, 200)
        
        query_count = len(connection.queries)
        print(f"Summary Queries: {query_count}")
        print(f"Summary Time: {time.time() - start_time:.4f}s")
        self.assertLess(query_count, 15)
