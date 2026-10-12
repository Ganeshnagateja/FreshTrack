from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Organization


class FoodCategory(models.Model):
    class Perishability(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    perishability = models.CharField(max_length=10, choices=Perishability.choices, default=Perishability.MEDIUM)
    storage_guidance = models.CharField(max_length=220, blank=True)
    default_alert_days = models.PositiveSmallIntegerField(default=3)
    default_storage_temperature = models.CharField(max_length=40, blank=True)
    icon = models.CharField(max_length=12, default="◈")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "food categories"

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    class Unit(models.TextChoices):
        KG = "kg", "Kilograms (kg)"
        G = "g", "Grams (g)"
        L = "L", "Litres (L)"
        ML = "ml", "Millilitres (ml)"
        PCS = "pcs", "Pieces"
        BOX = "box", "Boxes"
        PACK = "pack", "Packs"

    class Status(models.TextChoices):
        ACTIVE = "active", "In stock"
        DEPLETED = "depleted", "Out of stock"
        DISCARDED = "discarded", "Discarded / archived"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="inventory_items")
    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=80, blank=True, default="")
    barcode = models.CharField(max_length=100, blank=True, default="")
    category = models.ForeignKey(FoodCategory, on_delete=models.PROTECT, related_name="inventory_items")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.KG)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    received_date = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField(null=True, blank=True)
    alert_days = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Optional override for your category's default alert window.")
    storage_location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_inventory_items")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "sku"], condition=~Q(sku=""), name="uniq_org_sku_when_present"),
            models.UniqueConstraint(fields=["organization", "barcode"], condition=~Q(barcode=""), name="uniq_org_barcode_when_present"),
            models.CheckConstraint(condition=Q(quantity__gte=0), name="inventory_quantity_nonnegative"),
            models.CheckConstraint(condition=Q(reorder_level__gte=0), name="inventory_reorder_nonnegative"),
        ]
        indexes = [
            models.Index(fields=["organization", "status", "expiry_date"], name="inv_org_status_exp_idx"),
            models.Index(fields=["organization", "name"], name="inv_org_name_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def effective_alert_days(self):
        return self.alert_days if self.alert_days is not None else self.category.default_alert_days

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.localdate()).days

    @property
    def expiry_state(self):
        if self.status == self.Status.DISCARDED:
            return "discarded"
        if self.status == self.Status.DEPLETED:
            return "depleted"
        if not self.expiry_date:
            return "no-date"
        days = self.days_until_expiry
        if days < 0:
            return "expired"
        if days <= self.effective_alert_days:
            return "expiring"
        return "fresh"

    @property
    def is_low_stock(self):
        return self.status != self.Status.DISCARDED and self.quantity <= self.reorder_level


class ExpiryAlert(models.Model):
    class Kind(models.TextChoices):
        EXPIRING = "expiring", "Expiring soon"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="expiry_alerts")
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="expiry_alerts")
    alert_date = models.DateField(default=timezone.localdate)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "alert_date", "kind"], name="uniq_item_expiry_alert_day_kind")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.item.name}"
