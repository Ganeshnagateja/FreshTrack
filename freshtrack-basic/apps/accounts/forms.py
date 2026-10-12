from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils.text import slugify
from uuid import uuid4

from .models import Organization, User


class RegisterForm(UserCreationForm):
    organization_name = forms.CharField(max_length=140, label="Business or organization name")
    first_name = forms.CharField(max_length=150, label="Your name")
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "first_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["username"].help_text = "Used when you sign in."
        self.fields["password1"].help_text = "Use at least 8 characters and avoid common passwords."

    def save(self, commit=True):
        user = super().save(commit=False)
        org_name = self.cleaned_data["organization_name"].strip()
        user.first_name = self.cleaned_data["first_name"].strip()
        user.email = self.cleaned_data["email"].strip().lower()
        if not commit:
            # Match ModelForm semantics: don't write either the user or workspace yet.
            user._pending_organization_name = org_name
            return user

        base_slug = slugify(org_name)[:130] or "workspace"
        slug = f"{base_slug}-{uuid4().hex[:6]}"
        with transaction.atomic():
            organization = Organization.objects.create(name=org_name, slug=slug)
            user.organization = organization
            user.save()
        return user
