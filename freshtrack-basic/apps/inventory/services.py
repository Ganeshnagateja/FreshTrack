import csv
import io
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import FoodCategory, InventoryItem


CSV_COLUMNS = [
    "name", "category", "quantity", "unit", "expiry_date", "sku", "barcode",
    "received_date", "reorder_level", "storage_location", "alert_days", "notes",
]


def parse_decimal(value, *, default=None):
    value = (value or "").strip()
    if not value:
        return default
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"'{value}' is not a valid number") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("quantity values must be non-negative numbers")
    if max(-result.as_tuple().exponent, 0) > 3:
        raise ValueError("quantity values support up to 3 decimal places")
    if len(result.as_tuple().digits) > 12:
        raise ValueError("quantity value is too large")
    return result


def parse_optional_date(value, *, field_name):
    value = (value or "").strip()
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format")
    return parsed


def import_inventory_csv(uploaded_file, *, organization, actor):
    """Import CSV rows independently and report row-level validation errors."""
    try:
        raw = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("The CSV must be UTF-8 encoded.") from exc

    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        raise ValueError("The file is empty or has no header row.")
    normalized_headers = [header.strip().lower() for header in reader.fieldnames if header]
    missing = {"name", "category", "quantity"} - set(normalized_headers)
    if missing:
        raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))
    reader.fieldnames = normalized_headers

    imported = 0
    errors = []
    rows_seen = 0
    for line_number, row in enumerate(reader, start=2):
        rows_seen += 1
        row = {(key or "").strip().lower(): (value if isinstance(value, str) else "").strip()
               for key, value in row.items() if key is not None}
        if not any(row.values()):
            continue
        try:
            name = row.get("name", "")
            category_name = row.get("category", "")
            if not name:
                raise ValueError("name is required")
            if not category_name:
                raise ValueError("category is required")
            try:
                category = FoodCategory.objects.get(name__iexact=category_name)
            except FoodCategory.DoesNotExist as exc:
                raise ValueError(f"unknown category '{category_name}'") from exc

            quantity = parse_decimal(row.get("quantity"), default=Decimal("0"))
            reorder_level = parse_decimal(row.get("reorder_level"), default=Decimal("0"))
            received_date = parse_optional_date(row.get("received_date"), field_name="received_date")
            expiry_date = parse_optional_date(row.get("expiry_date"), field_name="expiry_date")
            raw_alert_days = row.get("alert_days", "").strip()
            if raw_alert_days:
                if not raw_alert_days.isdigit() or int(raw_alert_days) > 365:
                    raise ValueError("alert_days must be an integer from 0 to 365")
                alert_days = int(raw_alert_days)
            else:
                alert_days = None

            unit = (row.get("unit") or "kg").strip()
            allowed_units = {choice[0] for choice in InventoryItem.Unit.choices}
            if unit not in allowed_units:
                raise ValueError(f"unit must be one of: {', '.join(sorted(allowed_units))}")
            if received_date and expiry_date and expiry_date < received_date:
                raise ValueError("expiry_date cannot be earlier than received_date")

            with transaction.atomic():
                InventoryItem.objects.create(
                    organization=organization,
                    created_by=actor,
                    name=name[:160],
                    category=category,
                    quantity=quantity,
                    unit=unit,
                    sku=row.get("sku", "")[:80],
                    barcode=row.get("barcode", "")[:100],
                    received_date=received_date or timezone.localdate(),
                    expiry_date=expiry_date,
                    reorder_level=reorder_level,
                    alert_days=alert_days,
                    storage_location=row.get("storage_location", "")[:100],
                    notes=row.get("notes", ""),
                    status=InventoryItem.Status.ACTIVE if quantity > 0 else InventoryItem.Status.DEPLETED,
                )
            imported += 1
        except IntegrityError:
            errors.append({"line": line_number, "message": "Duplicate SKU or barcode in this workspace, or another database constraint was violated."})
        except (ValueError, ValidationError) as exc:
            errors.append({"line": line_number, "message": str(exc)})

    return {"imported": imported, "errors": errors, "rows_seen": rows_seen}
