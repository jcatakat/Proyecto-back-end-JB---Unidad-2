# dispositivos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.db.models import Count

from organizations.models import UserProfile
from ..models import Device, Measurement, AlertEvent, Category, Zone


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de scoping por organización
# ─────────────────────────────────────────────────────────────────────────────
def _is_global(user):
    # superuser o pertenece al grupo "EcoEnergy - Admin"
    return user.is_superuser or user.groups.filter(name="EcoEnergy - Admin").exists()

def _user_org(user):
    prof = getattr(user, "profile", None)
    return getattr(prof, "organization", None)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD Y LISTAS
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    """
    Muestra resumen: dispositivos por categoría/ zona, últimas alertas y mediciones.
    Respeta scoping por organización para usuarios no globales.
    """
    qs_devices = Device.objects.select_related("organization", "zone", "product", "product__category")
    qs_measurements = Measurement.objects.select_related("device")
    qs_alerts = AlertEvent.objects.select_related("device", "alert_rule")

    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            qs_devices = qs_devices.filter(organization=org)
            qs_measurements = qs_measurements.filter(device__organization=org)
            qs_alerts = qs_alerts.filter(device__organization=org)
        else:
            qs_devices = qs_devices.none()
            qs_measurements = qs_measurements.none()
            qs_alerts = qs_alerts.none()

    # Conteo de dispositivos por CATEGORÍA (a través de product__category)
    devices_by_category = (
        qs_devices.values("product__category__name")
        .annotate(total=Count("id"))
        .order_by("product__category__name")
    )

    # Conteo de dispositivos por ZONA
    devices_by_zone = (
        qs_devices.values("zone__name")
        .annotate(total=Count("id"))
        .order_by("zone__name")
    )

    alerts = qs_alerts.order_by("-occurred_at")[:5]
    measurements = qs_measurements.order_by("-measured_at")[:10]

    return render(
        request,
        "dashboard.html",
        {
            "devices_by_category": devices_by_category,  # [{product__category__name, total}]
            "devices_by_zone": devices_by_zone,          # [{zone__name, total}]
            "alerts": alerts,
            "measurements": measurements,
        },
    )


@login_required
def device_list(request):
    """
    Lista de dispositivos con filtros por categoría y zona.
    - category: id de Category (vía Device.product.category)
    - zone: id de Zone
    """
    category_filter = request.GET.get("category")
    zone_filter = request.GET.get("zone")

    devices = Device.objects.select_related("organization", "zone", "product", "product__category")

    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            devices = devices.filter(organization=org)
        else:
            devices = devices.none()

    if category_filter:
        devices = devices.filter(product__category_id=category_filter)
    if zone_filter:
        devices = devices.filter(zone_id=zone_filter)

    # Para los filtros del template
    categories = Category.objects.all().order_by("name")
    zones = Zone.objects.all().order_by("name")
    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            zones = zones.filter(organization=org)
        else:
            zones = zones.none()

    return render(
        request,
        "devices/device_list.html",
        {"devices": devices, "categories": categories, "zones": zones},
    )


@login_required
def device_detail(request, pk):
    """
    Detalle del dispositivo + sus mediciones/alertas.
    Respeta scoping por organización.
    """
    base_qs = Device.objects.select_related("organization", "zone", "product", "product__category")
    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            base_qs = base_qs.filter(organization=org)
        else:
            base_qs = base_qs.none()

    device = get_object_or_404(base_qs, pk=pk)

    measurements = (
        Measurement.objects.filter(device=device)
        .select_related("device")
        .order_by("-measured_at")
    )
    alerts = (
        AlertEvent.objects.filter(device=device)
        .select_related("device", "alert_rule")
        .order_by("-occurred_at")
    )

    return render(
        request,
        "devices/device_detail.html",
        {"device": device, "measurements": measurements, "alerts": alerts},
    )


@login_required
def measurement_list(request):
    """
    Listado de mediciones (últimas 50). Respeta scoping por organización.
    """
    measurements = Measurement.objects.select_related("device")

    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            measurements = measurements.filter(device__organization=org)
        else:
            measurements = measurements.none()

    measurements = measurements.order_by("-measured_at")[:50]
    return render(request, "measurements/measurement_list.html", {"measurements": measurements})


@login_required
def alert_list(request):
    """
    Listado de alertas (AlertEvent). Respeta scoping por organización.
    """
    alerts = AlertEvent.objects.select_related("device", "alert_rule")

    if not _is_global(request.user):
        org = _user_org(request.user)
        if org:
            alerts = alerts.filter(device__organization=org)
        else:
            alerts = alerts.none()

    alerts = alerts.order_by("-occurred_at")
    return render(request, "alerts/alert_list.html", {"alerts": alerts})

