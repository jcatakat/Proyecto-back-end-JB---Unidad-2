from django import forms
from django.contrib import admin, messages
from django.forms.models import BaseInlineFormSet

from .models import (
    Alert,
    Category,
    Device,
    Measurement,
    Organization,
    UserProfile,
    Zone,
)


class MeasurementInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            value = form.cleaned_data.get("value")
            if value is not None and value < 0:
                raise forms.ValidationError(
                    "Los valores de medición no pueden ser negativos."
                )


class MeasurementInline(admin.TabularInline):
    model = Measurement
    formset = MeasurementInlineFormSet
    extra = 1
    fields = ("value", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


class ScopedModelAdmin(admin.ModelAdmin):
    organization_lookup = "organization"

    def _user_profile(self, user):
        return getattr(user, "profile", None)

    def _user_is_global(self, user):
        profile = self._user_profile(user)
        return user.is_superuser or (
            profile is not None and profile.role == UserProfile.Role.ADMIN
        )

    def has_module_permission(self, request):
        if self._user_is_global(request.user):
            return True
        return super().has_module_permission(request)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if self._user_is_global(request.user):
            return queryset
        profile = self._user_profile(request.user)
        if profile and profile.organization_id:
            return queryset.filter(
                **{self.organization_lookup: profile.organization_id}
            )
        return queryset.none()

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        if not self._user_is_global(request.user) and "organization" in filters:
            filters.remove("organization")
        return filters

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if (
            not self._user_is_global(request.user)
            and self.organization_lookup == "organization"
        ):
            fields.append("organization")
        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            return None
        if self._user_is_global(request.user):
            return field
        profile = self._user_profile(request.user)
        if not profile or not profile.organization_id:
            return field
        related_model = db_field.remote_field.model
        if related_model is Organization:
            field.queryset = related_model.objects.filter(pk=profile.organization_id)
        elif hasattr(related_model, "organization"):
            field.queryset = related_model.objects.filter(
                organization=profile.organization
            )
        return field

    def save_model(self, request, obj, form, change):
        profile = self._user_profile(request.user)
        if (
            not self._user_is_global(request.user)
            and hasattr(obj, "organization")
            and profile
            and profile.organization
        ):
            obj.organization = profile.organization
        super().save_model(request, obj, form, change)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)

    def has_module_permission(self, request):
        profile = getattr(request.user, "profile", None)
        if request.user.is_superuser:
            return True
        if profile and profile.role == UserProfile.Role.ADMIN:
            return True
        return False


@admin.register(Category)
class CategoryAdmin(ScopedModelAdmin):
    list_display = ("name", "organization", "created_at")
    search_fields = ("name",)
    list_filter = ("organization",)
    ordering = ("name",)
    list_select_related = ("organization",)


@admin.register(Zone)
class ZoneAdmin(ScopedModelAdmin):
    list_display = ("name", "organization", "created_at")
    search_fields = ("name",)
    list_filter = ("organization",)
    ordering = ("name",)
    list_select_related = ("organization",)


@admin.register(Device)
class DeviceAdmin(ScopedModelAdmin):
    inlines = (MeasurementInline,)
    list_display = (
        "name",
        "category",
        "zone",
        "organization",
        "created_at",
    )
    search_fields = ("name", "category__name", "zone__name")
    list_filter = ("organization", "category", "zone")
    ordering = ("name",)
    list_select_related = ("organization", "category", "zone")


@admin.register(Measurement)
class MeasurementAdmin(ScopedModelAdmin):
    organization_lookup = "device__organization"
    list_display = ("device", "value", "created_at")
    search_fields = ("device__name",)
    list_filter = ("device__organization",)
    ordering = ("-created_at",)
    list_select_related = ("device", "device__organization")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            return None
        if db_field.name == "device" and not self._user_is_global(request.user):
            profile = self._user_profile(request.user)
            if profile and profile.organization:
                field.queryset = field.queryset.filter(
                    organization=profile.organization
                )
        return field


@admin.register(Alert)
class AlertAdmin(ScopedModelAdmin):
    organization_lookup = "device__organization"
    list_display = (
        "device",
        "severity",
        "message",
        "acknowledged",
        "created_at",
    )
    search_fields = ("device__name", "message")
    list_filter = ("device__organization", "severity", "acknowledged")
    ordering = ("-created_at",)
    list_select_related = ("device", "device__organization")

    @admin.action(description="Marcar alertas como atendidas")
    def marcar_alertas_atendidas(self, request, queryset):
        actualizadas = queryset.update(acknowledged=True)
        messages.success(
            request,
            f"{actualizadas} alerta(s) fueron marcadas como atendidas.",
        )

    actions = ("marcar_alertas_atendidas",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "updated_at")
    search_fields = ("user__username", "organization__name")
    list_filter = ("role", "organization")
    ordering = ("user__username",)
    list_select_related = ("user", "organization")
