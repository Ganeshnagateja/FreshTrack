from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.text import slugify
from uuid import uuid4

from .forms import RegisterForm
from .models import Organization


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"Your {user.organization.name} workspace is ready.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def organization_setup(request):
    if request.user.organization_id:
        return redirect("dashboard")
    if request.method == "POST":
        name = request.POST.get("organization_name", "").strip()
        if name:
            slug = f"{slugify(name)[:130] or 'workspace'}-{uuid4().hex[:6]}"
            with transaction.atomic():
                org = Organization.objects.create(name=name, slug=slug)
                request.user.organization = org
                request.user.save(update_fields=["organization"])
            messages.success(request, "Workspace created successfully.")
            return redirect("dashboard")
        messages.error(request, "Enter a business or organization name.")
    return render(request, "accounts/organization_setup.html")
