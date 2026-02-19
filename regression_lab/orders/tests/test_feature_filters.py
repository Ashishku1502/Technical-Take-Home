from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order

class OrderFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.c1 = Customer.objects.create(name="Alice", email="alice@example.com")
        self.c2 = Customer.objects.create(name="Bob", email="bob@test.com")
        
        self.o1 = Order.objects.create(customer=self.c1, status=Order.Status.PAID)
        self.o2 = Order.objects.create(customer=self.c1, status=Order.Status.DRAFT)
        self.o3 = Order.objects.create(customer=self.c2, status=Order.Status.SHIPPED)
        self.o4 = Order.objects.create(customer=self.c2, status=Order.Status.CANCELLED)

    def test_filter_by_status(self):
        # Filter by PAID
        res = self.client.get("/api/orders/?status=paid")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], self.o1.id)

        # Filter by DRAFT
        res = self.client.get("/api/orders/?status=draft")
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], self.o2.id)

    def test_filter_by_email_contains(self):
        # Filter by "ali" (should find Alice's orders: o1, o2)
        res = self.client.get("/api/orders/?email=ali")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 2)
        ids = sorted([r["id"] for r in res.data["results"]])
        expected = sorted([self.o1.id, self.o2.id])
        self.assertEqual(ids, expected)

        # Filter by "test.com" (should find Bob's orders: o3, o4)
        res = self.client.get("/api/orders/?email=test.com")
        self.assertEqual(len(res.data["results"]), 2)
        
    def test_filter_combined(self):
        # valid status + email match
        res = self.client.get("/api/orders/?status=shipped&email=bob")
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], self.o3.id)
        
        # valid status + no email match
        res = self.client.get("/api/orders/?status=shipped&email=alice")
        self.assertEqual(len(res.data["results"]), 0)
