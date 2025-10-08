from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from dispositivos.models import (
    Alert,
    Category,
    Device,
    Measurement,
    Organization,
    UserProfile,
    Zone,
)


class Command(BaseCommand):
    help = "Carga datos iniciales de organizaciones, dispositivos y usuarios de ejemplo."

    def handle(self, *args, **options):
        with transaction.atomic():
            organization, _ = Organization.objects.get_or_create(name="EcoEnergy")

            solar_category, _ = Category.objects.get_or_create(
                name="Panel Solar", organization=organization
            )
            wind_category, _ = Category.objects.get_or_create(
                name="Turbina Eólica", organization=organization
            )

            north_zone, _ = Zone.objects.get_or_create(
                name="Zona Norte", organization=organization
            )
            south_zone, _ = Zone.objects.get_or_create(
                name="Zona Sur", organization=organization
            )

            inverter, _ = Device.objects.get_or_create(
                name="Inversor Central",
                organization=organization,
                category=solar_category,
                zone=north_zone,
            )
            turbine, _ = Device.objects.get_or_create(
                name="Generador Principal",
                organization=organization,
                category=wind_category,
                zone=south_zone,
            )

            Measurement.objects.get_or_create(device=inverter, value=86.5)
            Measurement.objects.get_or_create(device=turbine, value=72.3)

            Alert.objects.get_or_create(
                device=inverter,
                severity=Alert.SEVERITY_CHOICES[0][0],
                message="Sobrecarga detectada en inversor",
            )
            Alert.objects.get_or_create(
                device=turbine,
                severity=Alert.SEVERITY_CHOICES[1][0],
                message="Vibración elevada",
            )

            self._ensure_users(organization)

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))

    def _ensure_users(self, organization):
        User = get_user_model()

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )
        if created:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password("Admin123!")
            admin_user.save()
        self._sync_profile(admin_user, organization, UserProfile.Role.ADMIN)

        analyst_user, created = User.objects.get_or_create(
            username="analista",
            defaults={"email": "analista@example.com", "is_staff": True},
        )
        if created:
            analyst_user.set_password("Analista123!")
            analyst_user.save()
        elif not analyst_user.is_staff:
            analyst_user.is_staff = True
            analyst_user.save()
        self._sync_profile(analyst_user, organization, UserProfile.Role.ANALYST)

        limited_permissions = [
            "view_device",
            "change_device",
            "view_measurement",
            "add_measurement",
            "change_measurement",
            "view_alert",
            "change_alert",
        ]
        permission_model = User._meta.get_field("user_permissions").remote_field.model
        permissions = permission_model.objects.filter(
            codename__in=limited_permissions,
            content_type__app_label="dispositivos",
        )
        analyst_user.user_permissions.set(permissions)

    def _sync_profile(self, user, organization, role):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.organization = organization
        profile.role = role
        profile.save()
