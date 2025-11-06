# accounts/views.py
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages

def logout_view(request):
    # Limpia claves de sesión opcionales (si no usas, se ignoran)
    for key in ("cart_id", "filtros_busqueda", "onboarding_step", "impersonating"):
        request.session.pop(key, None)

    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect("login")   # tu ruta de login ya existe en dispositivos/urls.py

# Create your views here.

# ─────────────────────────────────────────────────────────────────────────────
# AUTH BÁSICA (para flujos simples de login/registro)
# ─────────────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "Credenciales inválidas")
        else:
            messages.error(request, "Credenciales inválidas")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro exitoso, ahora puedes iniciar sesión")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def password_reset_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        messages.success(request, f"Se enviaron instrucciones a {email} (simulado)")
        return redirect("login")
    return render(request, "accounts/password_reset.html")
