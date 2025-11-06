# monitoreo/decorators.py
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def permission_or_redirect(perm_codename, redirect_to, msg="No tienes permisos para esta acción."):
    def _decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Inicia sesión para continuar.")
                return redirect("login")
            if not request.user.has_perm(perm_codename):
                messages.error(request, msg)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return _decorator
