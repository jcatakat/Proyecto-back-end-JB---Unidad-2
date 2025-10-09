# monitoreo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path("ping/", lambda r: HttpResponse("pong")),
    path("admin/", admin.site.urls),
    path("", include("dispositivos.urls")),  # ← incluye todas las rutas de la app
]

