# apps/dispositivos/admin.py
from django import forms
from django.contrib import admin, messages
from django.forms.models import BaseInlineFormSet
from organizations.models import Organization, UserProfile
from .models import (
    Category, Product, AlertRule, ProductAlertRule,
    Zone, Device, Measurement, AlertEvent
)

# ---- Inline para mediciones ----
class MeasurementInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            energy_kwh = form.cleaned_data.get("energy_kwh")
            if energy_kwh is not None and energy_kwh < 0:
                raise forms.ValidationError("Los valores de energía no pueden ser negativos.")

class MeasurementInline(admin.TabularInline):
    model = Measurement
    formset = MeasurementInlineFormSet
    extra = 1
    fields = ("energy_kwh", "measured_at")
    readonly_fields = ("measured_at",)
    ordering = ("-measured_at",)

# ---- Admin con scoping ----
class ScopedModelAdmin(admin.ModelAdmin):
    organization_lookup = "organization"

    def _user_profile(self, user):
        return getattr(user, "profile", None)

    def _user_is_global(self, user):
        return user.is_superuser or user.groups.filter(name="EcoEnergy - Admin").exists()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self._user_is_global(request.user):
            return qs
        prof = self._user_profile(request.user)
        if prof and prof.organization_id:
            return qs.filter(**{self.organization_lookup: prof.organization_id})
        return qs.none()

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        if not self._user_is_global(request.user) and "organization" in filters:
            filters.remove("organization")
        return filters

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if not self._user_is_global(request.user) and self.organization_lookup == "organization":
            fields.append("organization")
        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is None:
            return None
        if self._user_is_global(request.user):
            return field
        prof = self._user_profile(request.user)
        if not prof or not prof.organization_id:
            return field
        related_model = db_field.remote_field.model
        if related_model is Organization:
            field.queryset = related_model.objects.filter(pk=prof.organization_id)
        elif hasattr(related_model, "organization"):
            field.queryset = related_model.objects.filter(organization=prof.organization)
        return field

    def save_model(self, request, obj, form, change):
        prof = self._user_profile(request.user)
        if not self._user_is_global(request.user) and hasattr(obj, "organization") and prof and prof.organization:
            obj.organization = prof.organization
        super().save_model(request, obj, form, change)

# ---- Admins ----
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "sku", "status", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "sku", "manufacturer")
    ordering = ("name",)

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "unit", "status")
    list_filter = ("severity", "status")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(ProductAlertRule)
class ProductAlertRuleAdmin(admin.ModelAdmin):
    list_display = ("product", "alert_rule", "min_threshold", "max_threshold", "status")
    list_filter = ("product", "alert_rule")

@admin.register(Zone)
class ZoneAdmin(ScopedModelAdmin):
    list_display = ("name", "organization", "status", "created_at")
    list_filter = ("organization", "status")
    search_fields = ("name", "organization__name")
    ordering = ("organization", "name")

@admin.register(Device)
class DeviceAdmin(ScopedModelAdmin):
    inlines = (MeasurementInline,)
    list_display = ("name", "organization", "zone", "product", "max_power_w", "status", "created_at")
    list_filter = ("organization", "zone", "product", "status")
    search_fields = ("name", "zone__name", "product__name", "product__sku")
    ordering = ("organization", "name")

@admin.register(Measurement)
class MeasurementAdmin(ScopedModelAdmin):
    organization_lookup = "device__organization"
    list_display = ("device", "energy_kwh", "measured_at", "status")
    list_filter = ("device__organization",)
    ordering = ("-measured_at",)
    list_select_related = ("device", "device__organization")

@admin.register(AlertEvent)
class AlertEventAdmin(ScopedModelAdmin):
    organization_lookup = "device__organization"
    list_display = ("device", "alert_rule", "occurred_at", "status")
    list_filter = ("device__organization", "alert_rule__severity")
    ordering = ("-occurred_at",)
    list_select_related = ("device", "device__organization", "alert_rule")
