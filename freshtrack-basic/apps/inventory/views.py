import csv
from datetime import timedelta

from django.contrib import messages
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import tenant_required
from .forms import CSVImportForm, InventoryItemForm
from .models import ExpiryAlert, FoodCategory, InventoryItem
from .services import CSV_COLUMNS, import_inventory_csv


def _active_items(organization):
    return InventoryItem.objects.filter(organization=organization).exclude(status=InventoryItem.Status.DISCARDED)


@tenant_required
def dashboard(request):
    organization = request.user.organization
    today = timezone.localdate()
    items = _active_items(organization).select_related("category")
    expired_items = list(items.filter(status=InventoryItem.Status.ACTIVE, expiry_date__lt=today).order_by("expiry_date")[:6])
    candidates = items.filter(
        status=InventoryItem.Status.ACTIVE,
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=365),
    )
    all_expiring_items = sorted((item for item in candidates if item.expiry_state == "expiring"), key=lambda item: item.expiry_date)
    expiring_count = len(all_expiring_items)
    expiring_items = all_expiring_items[:6]
    context = {
        "active_nav": "dashboard",
        "total_count": items.count(),
        "expired_count": items.filter(status=InventoryItem.Status.ACTIVE, expiry_date__lt=today).count(),
        "expiring_count": expiring_count,
        "low_stock_count": items.filter(quantity__lte=F("reorder_level")).count(),
        "expired_items": expired_items,
        "expiring_items": expiring_items,
        "today": today,
    }
    return render(request, "inventory/dashboard.html", context)


@tenant_required
def inventory_list(request):
    organization = request.user.organization
    queryset = _active_items(organization).select_related("category")
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    expiry_filter = request.GET.get("expiry", "").strip()
    stock_filter = request.GET.get("stock", "").strip()

    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query))
    if category_id.isdigit():
        queryset = queryset.filter(category_id=int(category_id))
    if stock_filter == "low":
        queryset = queryset.filter(quantity__lte=F("reorder_level"))
    elif stock_filter == "in-stock":
        queryset = queryset.filter(status=InventoryItem.Status.ACTIVE)

    today = timezone.localdate()
    if expiry_filter == "expired":
        queryset = queryset.filter(status=InventoryItem.Status.ACTIVE, expiry_date__lt=today)
    elif expiry_filter == "expiring":
        queryset = queryset.filter(status=InventoryItem.Status.ACTIVE, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=365))
        queryset = [item for item in queryset if item.expiry_state == "expiring"]
    elif expiry_filter == "no-date":
        queryset = queryset.filter(expiry_date__isnull=True)

    queryset = list(queryset)
    queryset.sort(key=lambda item: (item.expiry_date is None, item.expiry_date or today + timedelta(days=9999), item.name.lower()))
    from django.core.paginator import Paginator
    page_obj = Paginator(queryset, 15).get_page(request.GET.get("page"))
    return render(request, "inventory/list.html", {
        "active_nav": "inventory", "page_obj": page_obj, "items": page_obj.object_list,
        "categories": FoodCategory.objects.all(), "q": query, "selected_category": category_id,
        "expiry_filter": expiry_filter, "stock_filter": stock_filter,
    })


@tenant_required
def inventory_create(request):
    form = InventoryItemForm(request.POST or None, organization=request.user.organization)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.organization = request.user.organization
        item.created_by = request.user
        item.status = InventoryItem.Status.ACTIVE if item.quantity > 0 else InventoryItem.Status.DEPLETED
        item.save()
        messages.success(request, f"{item.name} was added to inventory.")
        return redirect("inventory_list")
    return render(request, "inventory/item_form.html", {
        "active_nav": "inventory", "form": form,
        "page_title": "Add inventory item", "submit_label": "Save item",
    })


@tenant_required
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, organization=request.user.organization)
    form = InventoryItemForm(request.POST or None, instance=item, organization=request.user.organization)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = InventoryItem.Status.ACTIVE if updated.quantity > 0 else InventoryItem.Status.DEPLETED
        updated.save()
        messages.success(request, f"{updated.name} was updated.")
        return redirect("inventory_list")
    return render(request, "inventory/item_form.html", {
        "active_nav": "inventory", "form": form,
        "page_title": f"Edit {item.name}", "submit_label": "Save changes", "item": item,
    })


@tenant_required
def csv_template(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="freshtrack_inventory_template.csv"'
    writer = csv.DictWriter(response, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerow({
        "name": "Spinach", "category": "Vegetables & Fruits", "quantity": "8", "unit": "kg",
        "expiry_date": (timezone.localdate() + timedelta(days=3)).isoformat(), "sku": "VEG-001", "barcode": "890100000001",
        "received_date": timezone.localdate().isoformat(), "reorder_level": "2", "storage_location": "Cold room A",
        "alert_days": "", "notes": "Keep chilled",
    })
    return response


@tenant_required
def inventory_import(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        try:
            result = import_inventory_csv(form.cleaned_data["file"], organization=request.user.organization, actor=request.user)
        except ValueError as exc:
            form.add_error("file", str(exc))
        else:
            if result["imported"]:
                messages.success(request, f"Imported {result['imported']} inventory item(s).")
            if result["errors"]:
                messages.warning(request, f"{len(result['errors'])} row(s) need attention. See the import report below.")
    return render(request, "inventory/import.html", {
        "active_nav": "import", "form": form, "result": result, "csv_columns": CSV_COLUMNS,
    })


@tenant_required
def alert_center(request):
    organization = request.user.organization
    alerts = ExpiryAlert.objects.filter(organization=organization).select_related("item", "item__category")[:100]
    items = _active_items(organization).filter(status=InventoryItem.Status.ACTIVE, expiry_date__isnull=False).select_related("category")
    actionable = [item for item in items if item.expiry_state in {"expired", "expiring"}]
    actionable.sort(key=lambda item: item.expiry_date)
    return render(request, "inventory/alerts.html", {
        "active_nav": "alerts", "items": actionable, "alerts": alerts,
    })
