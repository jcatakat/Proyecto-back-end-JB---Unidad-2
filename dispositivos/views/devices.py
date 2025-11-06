# dispositivos/views/devices.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from dispositivos.models import Device
from dispositivos.forms import DeviceForm
from monitoreo.decorators import permission_or_redirect


@login_required
def device_list_advanced(request):
    q = (request.GET.get("q") or "").strip()
    sort = request.GET.get("sort", "name")

    if "page_size" in request.GET:
        try:
            request.session["device_page_size"] = int(request.GET.get("page_size") or 10)
        except ValueError:
            request.session["device_page_size"] = 10
    page_size = int(request.session.get("device_page_size", 10))

    qs = (
        Device.objects.select_related("organization", "zone", "product", "product__category")
        .order_by(sort)
    )

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(serial_number__icontains=q) |         # ← usa serial_number
            Q(organization__name__icontains=q) |
            Q(zone__name__icontains=q) |
            Q(product__name__icontains=q) |
            Q(product__category__name__icontains=q)
        )

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    ctx = {
        "page_obj": page_obj,
        "q": q,
        "sort": sort,
        "page_size": page_size,
        "querystring": querystring,
        "total": qs.count(),
    }
    return render(request, "devices/devices_list_paginador.html", ctx)


@login_required
@permission_or_redirect("dispositivos.add_device", "device_list_advanced", "No tienes permiso para crear dispositivos.")
def device_create(request):
    if request.method == "POST":
        form = DeviceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # ← guarda max_power_w y serial_number desde el form
            messages.success(request, "Dispositivo creado exitosamente")
            return redirect("device_list_advanced")
        messages.error(request, "Corrige los errores del formulario")
    else:
        form = DeviceForm()
    return render(request, "devices/device_form.html", {"form": form, "accion": "Crear"})


@login_required
@permission_or_redirect("dispositivos.change_device", "device_list_advanced", "No tienes permiso para editar dispositivos.")
def device_edit(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == "POST":
        form = DeviceForm(request.POST, request.FILES, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, "Dispositivo actualizado correctamente")
            return redirect("device_list_advanced")
        messages.error(request, "Corrige los errores del formulario")
    else:
        form = DeviceForm(instance=device)
    return render(request, "devices/device_form.html", {"form": form, "accion": "Editar"})


@login_required
@require_POST
def device_delete_ajax(request, pk):
    if not request.user.has_perm("dispositivos.delete_device"):
        return JsonResponse({"ok": False, "message": "No tienes permiso para eliminar."}, status=403)

    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return HttpResponseBadRequest("Solo AJAX")

    device = get_object_or_404(Device, pk=pk)
    nombre = getattr(device, "name", f"ID {device.pk}")
    device.delete()
    return JsonResponse({"ok": True, "message": f"Dispositivo '{nombre}' eliminado"})


@login_required
def device_export_xlsx(request):
    import openpyxl
    from openpyxl.utils import get_column_letter

    q = (request.GET.get("q") or "").strip()
    sort = request.GET.get("sort", "name")

    qs = (
        Device.objects.select_related("organization", "zone", "product", "product__category")
        .order_by(sort)
    )
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(serial_number__icontains=q) |         # ← usa serial_number
            Q(organization__name__icontains=q) |
            Q(zone__name__icontains=q) |
            Q(product__name__icontains=q) |
            Q(product__category__name__icontains=q)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dispositivos"

    headers = ["ID", "Nombre", "Serie", "Producto", "Categoría", "Zona", "Organización", "Potencia máx. (W)"]
    ws.append(headers)

    for d in qs:
        ws.append([
            d.id,
            d.name,
            d.serial_number or "",
            d.product.name if d.product_id else "",
            d.product.category.name if d.product_id and d.product.category_id else "",
            d.zone.name if d.zone_id else "",
            d.organization.name if d.organization_id else "",
            d.max_power_w,
        ])

    for col in ws.columns:
        length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(10, length + 2), 40)

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="dispositivos.xlsx"'
    wb.save(resp)
    return resp
