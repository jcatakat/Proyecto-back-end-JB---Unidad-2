# monitoreo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import logout_view
from django.conf.urls import handler403, handler404
from django.shortcuts import render

urlpatterns = [
    path("ping/",  lambda r: HttpResponse("pong")),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),


    # Rutas de tu app (home, etc.)
    path("", include("dispositivos.urls")),
]

# Servir archivos de MEDIA en desarrollo (por tu ImageField)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def custom_permission_denied_view(request, exception=None):
    return render(request, "403.html", status=403)

def custom_page_not_found_view(request, exception=None):
    return render(request, "404.html", status=404)

handler403 = custom_permission_denied_view
handler404 = custom_page_not_found_view


