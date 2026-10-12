from django.db import migrations


CATEGORIES = [
    {"name": "Vegetables & Fruits", "slug": "vegetables-fruits", "perishability": "high", "storage_guidance": "Handle gently; refrigerate suitable produce and keep leafy greens chilled.", "default_alert_days": 2, "default_storage_temperature": "Often 0–5°C; follow product guidance", "icon": "🥬"},
    {"name": "Dairy & Eggs", "slug": "dairy-eggs", "perishability": "high", "storage_guidance": "Keep refrigerated and follow the product's label and use-by date.", "default_alert_days": 3, "default_storage_temperature": "Typically 0–5°C", "icon": "🥛"},
    {"name": "Meat & Seafood", "slug": "meat-seafood", "perishability": "high", "storage_guidance": "Maintain cold-chain handling and separate raw products from ready-to-eat food.", "default_alert_days": 1, "default_storage_temperature": "Chilled ≤4°C; frozen ≤−18°C", "icon": "🐟"},
    {"name": "Bakery", "slug": "bakery", "perishability": "medium", "storage_guidance": "Store sealed in clean, dry conditions; monitor mould and product-specific dates.", "default_alert_days": 2, "default_storage_temperature": "Cool and dry; label dependent", "icon": "🍞"},
    {"name": "Dry Goods & Grains", "slug": "dry-goods-grains", "perishability": "low", "storage_guidance": "Keep sealed, dry, pest-protected and away from direct sunlight.", "default_alert_days": 14, "default_storage_temperature": "Cool, dry pantry", "icon": "🌾"},
    {"name": "Frozen Foods", "slug": "frozen-foods", "perishability": "low", "storage_guidance": "Keep frozen; avoid repeat thawing and refreezing.", "default_alert_days": 14, "default_storage_temperature": "Typically ≤−18°C", "icon": "❄️"},
    {"name": "Prepared Foods", "slug": "prepared-foods", "perishability": "high", "storage_guidance": "Use defined preparation, cooling, storage and discard procedures.", "default_alert_days": 1, "default_storage_temperature": "Follow food-safety procedure", "icon": "🥗"},
    {"name": "Beverages", "slug": "beverages", "perishability": "medium", "storage_guidance": "Follow label instructions; refrigerate after opening where required.", "default_alert_days": 5, "default_storage_temperature": "Label dependent", "icon": "🧃"},
    {"name": "Other", "slug": "other", "perishability": "medium", "storage_guidance": "Follow the product label and the organization's food-safety procedures.", "default_alert_days": 3, "default_storage_temperature": "Label dependent", "icon": "◈"},
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "FoodCategory")
    for category in CATEGORIES:
        Category.objects.update_or_create(slug=category["slug"], defaults=category)


def remove_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "FoodCategory")
    Category.objects.filter(slug__in=[category["slug"] for category in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]
    operations = [migrations.RunPython(seed_categories, remove_categories)]
