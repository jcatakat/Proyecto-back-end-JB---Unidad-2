from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Category, Device, Organization, UserProfile, Zone


class DeviceModelTests(TestCase):
    def setUp(self):
        self.org_primary = Organization.objects.create(name="EcoEnergy")
        self.org_secondary = Organization.objects.create(name="GreenPower")
        self.category_primary = Category.objects.create(
            name="Panel", organization=self.org_primary
        )
        self.zone_secondary = Zone.objects.create(
            name="Zona B", organization=self.org_secondary
        )

    def test_device_clean_validates_category_organization(self):
        device = Device(
            name="Medidor",  # nosec - valor de prueba
            category=self.category_primary,
            zone=Zone.objects.create(name="Zona A", organization=self.org_primary),
            organization=self.org_secondary,
        )
        with self.assertRaises(ValidationError) as ctx:
            device.full_clean()
        self.assertIn("category", ctx.exception.message_dict)

    def test_device_clean_validates_zone_organization(self):
        zone = self.zone_secondary
        device = Device(
            name="Sensor",  # nosec - valor de prueba
            category=self.category_primary,
            zone=zone,
            organization=self.org_primary,
        )
        with self.assertRaises(ValidationError) as ctx:
            device.full_clean()
        self.assertIn("zone", ctx.exception.message_dict)


class SeedCommandTests(TestCase):
    def test_seed_command_creates_users_and_profiles(self):
        call_command("seed_initial_data")
        User = get_user_model()

        admin_user = User.objects.get(username="admin")
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.profile.role, UserProfile.Role.ADMIN)

        analyst = User.objects.get(username="analista")
        self.assertTrue(analyst.is_staff)
        self.assertEqual(analyst.profile.role, UserProfile.Role.ANALYST)
        self.assertIsNotNone(analyst.profile.organization)
