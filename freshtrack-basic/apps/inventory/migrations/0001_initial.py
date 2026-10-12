import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FoodCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=90, unique=True)),
                ("perishability", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium", max_length=10)),
                ("storage_guidance", models.CharField(blank=True, max_length=220)),
                ("default_alert_days", models.PositiveSmallIntegerField(default=3)),
                ("default_storage_temperature", models.CharField(blank=True, max_length=40)),
                ("icon", models.CharField(default="◈", max_length=12)),
            ],
            options={"verbose_name_plural": "food categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("sku", models.CharField(blank=True, default="", max_length=80)),
                ("barcode", models.CharField(blank=True, default="", max_length=100)),
                ("quantity", models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ("unit", models.CharField(choices=[("kg", "Kilograms (kg)"), ("g", "Grams (g)"), ("L", "Litres (L)"), ("ml", "Millilitres (ml)"), ("pcs", "Pieces"), ("box", "Boxes"), ("pack", "Packs")], default="kg", max_length=8)),
                ("reorder_level", models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ("received_date", models.DateField(default=django.utils.timezone.localdate)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("alert_days", models.PositiveSmallIntegerField(blank=True, help_text="Optional override for your category's default alert window.", null=True)),
                ("storage_location", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("active", "In stock"), ("depleted", "Out of stock"), ("discarded", "Discarded / archived")], default="active", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_inventory_items", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="inventory_items", to="inventory.foodcategory")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory_items", to="accounts.organization")),
            ],
            options={"ordering": ["expiry_date", "name"]},
        ),
        migrations.CreateModel(
            name="ExpiryAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_date", models.DateField(default=django.utils.timezone.localdate)),
                ("kind", models.CharField(choices=[("expiring", "Expiring soon"), ("expired", "Expired")], max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expiry_alerts", to="inventory.inventoryitem")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expiry_alerts", to="accounts.organization")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.UniqueConstraint(condition=~models.Q(("sku", "")), fields=("organization", "sku"), name="uniq_org_sku_when_present"),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.UniqueConstraint(condition=~models.Q(("barcode", "")), fields=("organization", "barcode"), name="uniq_org_barcode_when_present"),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gte", 0)), name="inventory_quantity_nonnegative"),
        ),
        migrations.AddConstraint(
            model_name="inventoryitem",
            constraint=models.CheckConstraint(condition=models.Q(("reorder_level__gte", 0)), name="inventory_reorder_nonnegative"),
        ),
        migrations.AddConstraint(
            model_name="expiryalert",
            constraint=models.UniqueConstraint(fields=("item", "alert_date", "kind"), name="uniq_item_expiry_alert_day_kind"),
        ),
        migrations.AddIndex(
            model_name="inventoryitem",
            index=models.Index(fields=["organization", "status", "expiry_date"], name="inv_org_status_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="inventoryitem",
            index=models.Index(fields=["organization", "name"], name="inv_org_name_idx"),
        ),
    ]
