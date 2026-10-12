from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Organization, User
from .models import FoodCategory, InventoryItem
from .services import import_inventory_csv


class BasicInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name="Sample Store", slug="sample-store-test")
        cls.user = User.objects.create_user(
            username="inventory-user",
            password="local-test-password",
            email="inventory@example.test",
            organization=cls.organization,
        )
        cls.category = FoodCategory.objects.get(slug="vegetables-fruits")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_dashboard_loads(self):
        self.client.login(username="inventory-user", password="local-test-password")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Expiry watchlist")

    def test_create_item(self):
        self.client.login(username="inventory-user", password="local-test-password")
        response = self.client.post(reverse("inventory_create"), {
            "name": "Test Spinach",
            "category": self.category.pk,
            "quantity": "4.000",
            "unit": "kg",
            "reorder_level": "1.000",
            "received_date": timezone.localdate().isoformat(),
            "expiry_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "alert_days": "",
            "sku": "TEST-SPINACH-01",
            "barcode": "",
            "storage_location": "Cold room",
            "notes": "For automated test",
        })
        self.assertEqual(response.status_code, 302)
        item = InventoryItem.objects.get(name="Test Spinach", organization=self.organization)
        self.assertEqual(item.quantity, Decimal("4.000"))
        self.assertEqual(item.expiry_state, "expiring")

    def test_csv_import_creates_inventory_item(self):
        payload = (
            "name,category,quantity,unit,received_date,expiry_date,sku\n"
            f"Test Milk,Dairy & Eggs,2,L,{timezone.localdate().isoformat()},,TEST-MILK-01\n"
        ).encode("utf-8")
        upload = SimpleUploadedFile("items.csv", payload, content_type="text/csv")
        result = import_inventory_csv(upload, organization=self.organization, actor=self.user)
        self.assertEqual(result["imported"], 1)
        self.assertEqual(result["errors"], [])
        self.assertTrue(InventoryItem.objects.filter(organization=self.organization, name="Test Milk").exists())
