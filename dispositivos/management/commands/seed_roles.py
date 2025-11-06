# dispositivos/management/commands/seed_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from dispositivos.models import Zone, Device
from organizations.models import Organization

# UserProfile es opcional según tu proyecto; si no existe, seguimos sin perfilar.
try:
    from organizations.models import UserProfile  # type: ignore
    HAS_PROFILE = True
except Exception:
    HAS_PROFILE = False


def ensure_group(name: str, perms: list[Permission]) -> Group:
    g, _ = Group.objects.get_or_create(name=name)
    # Para ser idempotente: une permisos actuales + nuevos
    actual = set(g.permissions.all())
    nuevo = set(perms)
    g.permissions.set(list(actual | nuevo))
    g.save()
    return g


class Command(BaseCommand):
    help = "Crea grupos, permisos y usuarios demo para EcoEnergy"

    def handle(self, *args, **options):
        User = get_user_model()

        # ────────────────────────────────────────────────────────────────────
        # 1) Organización base (útil para tus vistas con scoping por org)
        # ────────────────────────────────────────────────────────────────────
        org, _ = Organization.objects.get_or_create(name="Cliente Demo SpA")

        # ────────────────────────────────────────────────────────────────────
        # 2) Permisos por modelo (Zone, Device)
        # ────────────────────────────────────────────────────────────────────
        ct_zone = ContentType.objects.get_for_model(Zone)
        ct_dev = ContentType.objects.get_for_model(Device)

        zone_perms = Permission.objects.filter(
            content_type=ct_zone,
            codename__in=["view_zone", "add_zone", "change_zone", "delete_zone"],
        )
        dev_perms = Permission.objects.filter(
            content_type=ct_dev,
            codename__in=["view_device", "add_device", "change_device", "delete_device"],
        )
        zone_view = zone_perms.filter(codename="view_zone")
        dev_view = dev_perms.filter(codename="view_device")

        # ────────────────────────────────────────────────────────────────────
        # 3) Grupos
        # ────────────────────────────────────────────────────────────────────
        g_admin_zonas = ensure_group("Admin zonas", list(zone_perms))
        g_admin_devs = ensure_group("Admin dispositivos", list(dev_perms))
        g_solo_lectura = ensure_group(
            "Solo lectura", list(zone_view) + list(dev_view)
        )

        # ────────────────────────────────────────────────────────────────────
        # 4) Usuarios demo (no superusers) + perfiles (si existen)
        # ────────────────────────────────────────────────────────────────────
        usuarios = [
            # username, email, password, grupo
            ("admin_zonas", "admin_zonas@example.com", "ChangeMe123!", g_admin_zonas),
            ("admin_dispositivos", "admin_dispositivos@example.com", "ChangeMe123!", g_admin_devs),
            ("visor_demo", "visor@example.com", "ChangeMe123!", g_solo_lectura),
        ]

        for username, email, pwd, grupo in usuarios:
            u, created = User.objects.get_or_create(username=username, defaults={"email": email})
            if created:
                u.set_password(pwd)
                u.is_staff = True  # útil para entrar a /admin si quieres
                u.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username} / {pwd}"))
            else:
                self.stdout.write(f"Usuario existente: {username}")

            # asegura pertenencia al grupo
            u.groups.add(grupo)

            # crea/actualiza perfil con organización, si tu proyecto lo usa
            if HAS_PROFILE:
                prof, _ = UserProfile.objects.get_or_create(user=u, defaults={"organization": org})
                if prof.organization_id != org.id:
                    prof.organization = org
                    prof.save()

        # ────────────────────────────────────────────────────────────────────
        # 5) Mensaje final
        # ────────────────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\nSemilla completada:"))
        self.stdout.write(f"  - Organización: {org.name}")
        self.stdout.write("  - Grupos: Admin zonas, Admin dispositivos, Solo lectura")
        self.stdout.write("  - Usuarios:")
        self.stdout.write("      • admin_zonas / ChangeMe123!")
        self.stdout.write("      • admin_dispositivos / ChangeMe123!")
        self.stdout.write("      • visor_demo / ChangeMe123!")
        self.stdout.write("\nTip: inicia sesión con esos usuarios para probar permisos.")
