from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order

class SummarySortingTest(TestCase):
    def test_summary_sorting_nulls_last(self):
        client = APIClient()
        
        # High spender
        c1 = Customer.objects.create(name="Rich", email="rich@test.com")
        o1 = Order.objects.create(customer=c1, status=Order.Status.PAID, total_cents=1000)
        
        # Zero spender (no orders)
        c2 = Customer.objects.create(name="Poor", email="poor@test.com")
        
        # Zero spender (unpaid orders only)
        c3 = Customer.objects.create(name="Draft", email="draft@test.com")
        o3 = Order.objects.create(customer=c3, status=Order.Status.DRAFT, total_cents=5000)

        res = client.get("/api/orders/summary/?limit=10")
        rows = res.data["rows"]
        
        # Expect Rich to be first (1000 > 0)
        # If NULLS FIRST bug exists, Poor/Draft (None) might be first.
        self.assertEqual(rows[0]["customer_id"], c1.id)
        self.assertEqual(rows[0]["total_cents"], 1000)
        
        self.assertEqual(len(rows), 3)
