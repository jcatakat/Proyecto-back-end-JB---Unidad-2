from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User, Group

from organizations.models import Organization, UserProfile
from dispositivos.models import Zone, Device, Product

class Command(BaseCommand):
    help = "Crea una organización demo con zonas, dispositivos y usuarios con perfiles/roles."

    @transaction.atomic
    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name="Cliente Demo SpA")

        # Zonas
        z1, _ = Zone.objects.get_or_create(organization=org, name="Oficina 1")
        z2, _ = Zone.objects.get_or_create(organization=org, name="Data Center")

        # Productos (deben existir por seed_catalog_es)
        p_led = Product.objects.get(sku="LED-40W")
        p_ac  = Product.objects.get(sku="AC-9000")

        # Dispositivos
        d1, _ = Device.objects.get_or_create(
            organization=org, zone=z1, product=p_led, name="Panel LED Sala Reuniones",
            defaults=dict(max_power_w=40),
        )
        d2, _ = Device.objects.get_or_create(
            organization=org, zone=z2, product=p_ac, name="A/C Rack 1",
            defaults=dict(max_power_w=2000),
        )

        # Usuarios y perfiles (roles/grupos deben existir por seed_roles_modules)
        g_admin, _ = Group.objects.get_or_create(name="Cliente - Admin")
        g_elec, _  = Group.objects.get_or_create(name="Cliente - Electrónico")

        # Cliente Admin
        u1, created = User.objects.get_or_create(username="cliente_admin", defaults={"email":"admin@demo.cl"})
        if created:
            u1.set_password("Demo1234!")
            u1.save()
        u1.groups.add(g_admin)
        UserProfile.objects.get_or_create(user=u1, defaults={"organization": org, "rut": "11.111.111-1"})

        # Cliente Electrónico
        u2, created = User.objects.get_or_create(username="cliente_tec", defaults={"email":"tec@demo.cl"})
        if created:
            u2.set_password("Demo1234!")
            u2.save()
        u2.groups.add(g_elec)
        UserProfile.objects.get_or_create(user=u2, defaults={"organization": org, "rut": "22.222.222-2"})

        self.stdout.write(self.style.SUCCESS("Demo de organización/zonas/dispositivos/usuarios creada."))
