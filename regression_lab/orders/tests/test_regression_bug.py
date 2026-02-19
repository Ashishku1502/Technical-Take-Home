from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order

class RegressionBugTests(TestCase):
    def test_cancelling_order_does_not_delete_customer(self):
        client = APIClient()
        c = Customer.objects.create(name="Alice", email="alice@example.com")
        o = Order.objects.create(customer=c, status=Order.Status.PAID)

        res = client.post(f"/api/orders/{o.id}/cancel/")
        self.assertEqual(res.status_code, 200)

        # Customer should still exist (this currently FAILS due to an intentional bug)
        self.assertTrue(Customer.objects.filter(id=c.id).exists())

    def test_cancelling_order_preserves_other_orders(self):
        client = APIClient()
        c = Customer.objects.create(name="Bob", email="bob@example.com")
        o1 = Order.objects.create(customer=c, status=Order.Status.PAID)
        o2 = Order.objects.create(customer=c, status=Order.Status.PAID)

        res = client.post(f"/api/orders/{o1.id}/cancel/")
        self.assertEqual(res.status_code, 200)

        self.assertTrue(Customer.objects.filter(id=c.id).exists())
        self.assertTrue(Order.objects.filter(id=o2.id).exists())
        
        o1.refresh_from_db()
        self.assertEqual(o1.status, Order.Status.CANCELLED)
