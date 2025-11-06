# dispositivos/urls.py
from django.urls import path
from .views import base, zones, devices

urlpatterns = [
    # Home / dashboard y vistas existentes
    path("", base.dashboard, name="dashboard"),
    path("devices/", base.device_list, name="device_list"),
    path("devices/<int:pk>/", base.device_detail, name="device_detail"),
    path("measurements/", base.measurement_list, name="measurement_list"),
    path("alerts/", base.alert_list, name="alert_list"),

    # Zonas (CRUD + borrar por AJAX + exportar)
    path("zonas/", zones.zona_list, name="zona_list"),
    path("zonas/nueva/", zones.zona_create, name="zona_create"),
    path("zonas/editar/<int:pk>/", zones.zona_edit, name="zona_edit"),
    path("zonas/<int:pk>/eliminar/", zones.zona_delete_ajax, name="zona_delete_ajax"),
    path("zonas/exportar/", zones.zona_export_xlsx, name="zona_export"),


    path("dispositivos/", devices.device_list_advanced, name="device_list_advanced"),
    path("dispositivos/nuevo/", devices.device_create, name="device_create"),
    path("dispositivos/<int:pk>/editar/", devices.device_edit, name="device_edit"),
    path("dispositivos/<int:pk>/eliminar/", devices.device_delete_ajax, name="device_delete_ajax"),
    path("dispositivos/exportar/", devices.device_export_xlsx, name="device_export"),
]
