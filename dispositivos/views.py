# dispositivos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.db.models import Count

from .models import Device, Measurement, Alert, Category, Zone

# -----------------------
# DASHBOARD Y LISTAS
# -----------------------

@login_required
def dashboard(request):
    # Conteos por categoría y por zona (no dependen de user)
    devices_by_category = (
        Device.objects.values("category__name")
        .annotate(total=Count("id"))
        .order_by("category__name")
    )
    devices_by_zone = (
        Device.objects.values("zone__name")
        .annotate(total=Count("id"))
        .order_by("zone__name")
    )

    alerts = Alert.objects.select_related("device").order_by("-created_at")[:5]
    measurements = (
        Measurement.objects.select_related("device")
        .order_by("-created_at")[:10]
    )

    return render(
        request,
        "dashboard.html",
        {
            "devices_by_category": devices_by_category,  # lista de dicts {category__name, total}
            "devices_by_zone": devices_by_zone,          # lista de dicts {zone__name, total}
            "alerts": alerts,
            "measurements": measurements,
        },
    )


@login_required
def device_list(request):
    category_filter = request.GET.get("category")
    zone_filter = request.GET.get("zone")

    devices = Device.objects.select_related("category", "zone").all()
    if category_filter:
        devices = devices.filter(category_id=category_filter)
    if zone_filter:
        devices = devices.filter(zone_id=zone_filter)

    categories = Category.objects.all().order_by("name")
    zones = Zone.objects.all().order_by("name")

    return render(
        request,
        "devices/device_list.html",
        {"devices": devices, "categories": categories, "zones": zones},
    )


@login_required
def device_detail(request, pk):
    # ❌ No usar request.user.organization (tu User no lo tiene)
    device = get_object_or_404(Device.objects.select_related("category", "zone"), pk=pk)
    measurements = Measurement.objects.filter(device=device).order_by("-created_at")
    alerts = Alert.objects.filter(device=device).order_by("-created_at")
    return render(
        request,
        "devices/device_detail.html",
        {"device": device, "measurements": measurements, "alerts": alerts},
    )


@login_required
def measurement_list(request):
    # Mostrar todas las mediciones (si luego agregas User.organization, aquí filtras por eso)
    measurements = (
        Measurement.objects.select_related("device")
        .order_by("-created_at")[:50]
    )
    return render(request, "measurements/measurement_list.html", {"measurements": measurements})


@login_required
def alert_list(request):
    alerts = Alert.objects.select_related("device").order_by("-created_at")
    return render(request, "alerts/alert_list.html", {"alerts": alerts})


# -----------------------
# AUTH BÁSICA
# -----------------------

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
    return render(request, "auth/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro exitoso, ahora puedes iniciar sesión")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "auth/register.html", {"form": form})


def password_reset_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        messages.success(request, f"Se enviaron instrucciones a {email} (simulado)")
        return redirect("login")
    return render(request, "auth/password_reset.html")
