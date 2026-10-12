from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def tenant_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.organization_id:
            messages.warning(request, "Set up a workspace before opening inventory.")
            return redirect("organization_setup")
        return view_func(request, *args, **kwargs)
    return wrapped
