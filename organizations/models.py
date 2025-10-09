# apps/organizations/models.py
from django.db import models
from django.conf import settings

class Organization(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = "organization"
        ordering = ["name"]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "EcoEnergy Admin (Global)"
        CLIENT_ADMIN = "CLIENT_ADMIN", "Cliente - Admin"
        CLIENT_ELECTRONIC = "CLIENT_ELECTRONIC", "Cliente - Electrónico"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="members", null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT_ADMIN)

    # Extras (opcionales, según tu base anterior)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)

    class Meta:
        db_table = "user_profile"
        ordering = ["user__username"]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        org = self.organization.name if self.organization else "GLOBAL"
        return f"{self.user.username} @ {org} [{self.role}]"
