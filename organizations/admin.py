# apps/organizations/admin.py
from django.contrib import admin
from .models import Organization, UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("organization", "role")
    search_fields = ("user__username", "organization__name")
    ordering = ("organization__name", "user__username")
