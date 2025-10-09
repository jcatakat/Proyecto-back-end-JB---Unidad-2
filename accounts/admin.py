# apps/accounts/admin.py
from django.contrib import admin
from .models import Module, Role, RoleModulePermission


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "icon")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("group",)
    search_fields = ("group__name",)
    ordering = ("group__name",)


@admin.register(RoleModulePermission)
class RoleModulePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "module", "can_view", "can_add", "can_change", "can_delete")
    list_filter = ("role", "module")
    list_editable = ("can_view", "can_add", "can_change", "can_delete")
    search_fields = ("role__group__name", "module__code", "module__name")
