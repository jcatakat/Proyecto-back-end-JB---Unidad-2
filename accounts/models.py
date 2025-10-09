# apps/accounts/models.py
from django.db import models
from django.contrib.auth.models import Group

class Module(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "module"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Role(models.Model):
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="role"
    )

    class Meta:
        db_table = "role"

    def __str__(self):
        return self.group.name


class RoleModulePermission(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="module_perms"
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="role_perms"
    )
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_change = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "role_module_permission"
        unique_together = ("role", "module")
        verbose_name = "Role-Module Permission"
        verbose_name_plural = "Role-Module Permissions"

    def __str__(self):
        return f"{self.role} → {self.module}"
