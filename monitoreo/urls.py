"""
URL configuration for monitoreo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dispositivos import views
from django.http import HttpResponse



urlpatterns = [
    path("ping/", lambda r: HttpResponse("pong")),
    path('admin/', admin.site.urls),
    path("", views.dashboard, name="dashboard"),  
    path("devices/", views.device_list, name="device_list"), 
    path("devices/<int:pk>/", views.device_detail, name="device_detail"), 
    path("measurements/", views.measurement_list, name="measurement_list"), 
    path("alerts/", views.alert_list, name="alert_list"),  
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("password-reset/", views.password_reset_view, name="password_reset"),

]
