# accounts/urls.py
from django.urls import path
from accounts.views import logout_view
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
]
