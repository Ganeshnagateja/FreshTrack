from django import forms
from django.core.exceptions import ValidationError

from .models import FoodCategory, InventoryItem


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name", "category", "sku", "barcode", "quantity", "unit", "reorder_level",
            "received_date", "expiry_date", "alert_days", "storage_location", "notes",
        ]
        widgets = {
            "received_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "expiry_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["category"].queryset = FoodCategory.objects.all()
        for field_name in ("sku", "barcode", "storage_location", "notes", "expiry_date"):
            self.fields[field_name].required = False
        self.fields["alert_days"].required = False
        self.fields["alert_days"].widget.attrs.update({"min": 0, "max": 365, "placeholder": "Use category default"})
        self.fields["received_date"].input_formats = ["%Y-%m-%d"]
        self.fields["expiry_date"].input_formats = ["%Y-%m-%d"]
        self.fields["quantity"].widget.attrs.update({"min": "0", "step": "0.001"})
        self.fields["reorder_level"].widget.attrs.update({"min": "0", "step": "0.001"})

    def clean(self):
        cleaned = super().clean()
        received = cleaned.get("received_date")
        expiry = cleaned.get("expiry_date")
        if received and expiry and expiry < received:
            self.add_error("expiry_date", "Expiry date cannot be earlier than the received date.")
        if cleaned.get("alert_days") is not None and cleaned["alert_days"] > 365:
            self.add_error("alert_days", "Use an alert window from 0 to 365 days, or leave it blank for the category default.")
        if cleaned.get("quantity") is not None and cleaned["quantity"] < 0:
            self.add_error("quantity", "Quantity cannot be negative.")
        if cleaned.get("reorder_level") is not None and cleaned["reorder_level"] < 0:
            self.add_error("reorder_level", "Reorder level cannot be negative.")
        if self.organization:
            for field_name, label in (("sku", "SKU"), ("barcode", "Barcode")):
                value = (cleaned.get(field_name) or "").strip()
                if not value:
                    continue
                duplicates = InventoryItem.objects.filter(organization=self.organization, **{field_name: value})
                if self.instance.pk:
                    duplicates = duplicates.exclude(pk=self.instance.pk)
                if duplicates.exists():
                    self.add_error(field_name, f"This {label.lower()} is already in use in this workspace.")
        return cleaned


class CSVImportForm(forms.Form):
    file = forms.FileField(help_text="CSV only · up to 5 MB")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update({"class": "form-control", "accept": ".csv,text/csv"})

    def clean_file(self):
        file = self.cleaned_data["file"]
        if not file.name.lower().endswith(".csv"):
            raise ValidationError("Please upload a .csv file.")
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("CSV files must be 5 MB or smaller.")
        return file
