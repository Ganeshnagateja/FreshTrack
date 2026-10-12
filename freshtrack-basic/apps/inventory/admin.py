from django.contrib import admin
from .models import ExpiryAlert, FoodCategory, InventoryItem


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "perishability", "default_alert_days", "default_storage_temperature")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "category", "quantity", "unit", "expiry_date", "status")
    list_filter = ("organization", "category", "status", "expiry_date")
    search_fields = ("name", "sku", "barcode")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ExpiryAlert)
class ExpiryAlertAdmin(admin.ModelAdmin):
    list_display = ("organization", "item", "alert_date", "kind", "created_at")
    list_filter = ("organization", "kind", "alert_date")
