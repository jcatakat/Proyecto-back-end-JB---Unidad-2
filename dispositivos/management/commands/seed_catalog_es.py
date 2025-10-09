from django.core.management.base import BaseCommand
from django.db import transaction

from dispositivos.models import (
    Category,
    Product,
    AlertRule,
    ProductAlertRule,
)

class Command(BaseCommand):
    help = "Carga catálogo base en español: categorías, productos, reglas de alerta y overrides (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        # ─────────────────────────────────────────────
        # Categorías (globales)
        # ─────────────────────────────────────────────
        cat_il, _ = Category.objects.get_or_create(name="Iluminación")
        cat_cl, _ = Category.objects.get_or_create(name="Climatización")
        cat_co, _ = Category.objects.get_or_create(name="Computación")

        # ─────────────────────────────────────────────
        # Productos del catálogo (globales)
        # ─────────────────────────────────────────────
        p1, _ = Product.objects.get_or_create(
            sku="LED-40W",
            defaults=dict(
                name="Panel LED 40W",
                category=cat_il,
                manufacturer="EcoLuz",
                model_name="PL-40",
                description="Panel LED para oficinas con alta eficiencia.",
                nominal_voltage_v=220.0,
                max_current_a=0.25,
                standby_power_w=1.0,
            ),
        )
        p1.name = "Panel LED 40W"; p1.category = cat_il
        p1.manufacturer = "EcoLuz"; p1.model_name = "PL-40"
        p1.description = "Panel LED para oficinas con alta eficiencia."
        p1.nominal_voltage_v = 220.0; p1.max_current_a = 0.25; p1.standby_power_w = 1.0
        p1.save()

        p2, _ = Product.objects.get_or_create(
            sku="AC-9000",
            defaults=dict(
                name="Aire Acondicionado 9000 BTU",
                category=cat_cl,
                manufacturer="ClimaTech",
                model_name="CT-9K",
                description="Split mural para sala pequeña.",
                nominal_voltage_v=220.0,
                max_current_a=4.5,
                standby_power_w=2.0,
            ),
        )
        p2.name = "Aire Acondicionado 9000 BTU"; p2.category = cat_cl
        p2.manufacturer = "ClimaTech"; p2.model_name = "CT-9K"
        p2.description = "Split mural para sala pequeña."
        p2.nominal_voltage_v = 220.0; p2.max_current_a = 4.5; p2.standby_power_w = 2.0
        p2.save()

        p3, _ = Product.objects.get_or_create(
            sku="PC-ESCR-A",
            defaults=dict(
                name="PC Escritorio A",
                category=cat_co,
                manufacturer="CompuWare",
                model_name="CW-Desk-A",
                description="Equipo de oficina estándar.",
                nominal_voltage_v=220.0,
                max_current_a=1.2,
                standby_power_w=3.0,
            ),
        )
        p3.name = "PC Escritorio A"; p3.category = cat_co
        p3.manufacturer = "CompuWare"; p3.model_name = "CW-Desk-A"
        p3.description = "Equipo de oficina estándar."
        p3.nominal_voltage_v = 220.0; p3.max_current_a = 1.2; p3.standby_power_w = 3.0
        p3.save()

        # ─────────────────────────────────────────────
        # Reglas de alerta (globales)
        # ─────────────────────────────────────────────
        r1, _ = AlertRule.objects.get_or_create(
            name="Consumo alto",
            severity=AlertRule.Severity.HIGH,
            defaults=dict(unit="kWh", default_max_threshold=50.0),
        ); r1.unit="kWh"; r1.default_max_threshold=50.0; r1.save()

        r2, _ = AlertRule.objects.get_or_create(
            name="Consumo en espera elevado",
            severity=AlertRule.Severity.MEDIUM,
            defaults=dict(unit="kWh", default_max_threshold=0.5),
        ); r2.unit="kWh"; r2.default_max_threshold=0.5; r2.save()

        r3, _ = AlertRule.objects.get_or_create(
            name="Bajo rendimiento",
            severity=AlertRule.Severity.LOW,
            defaults=dict(unit="kWh", default_min_threshold=0.5),
        ); r3.unit="kWh"; r3.default_min_threshold=0.5; r3.save()

        r4, _ = AlertRule.objects.get_or_create(
            name="Temperatura fuera de rango",
            severity=AlertRule.Severity.CRITICAL,
            defaults=dict(unit="°C", default_min_threshold=16.0, default_max_threshold=28.0),
        ); r4.unit="°C"; r4.default_min_threshold=16.0; r4.default_max_threshold=28.0; r4.save()

        # ─────────────────────────────────────────────
        # Overrides por producto (join table)
        # ─────────────────────────────────────────────
        ProductAlertRule.objects.update_or_create(
            product=p1, alert_rule=r2,
            defaults=dict(min_threshold=None, max_threshold=1.5, unit_override="kWh"),
        )
        ProductAlertRule.objects.update_or_create(
            product=p2, alert_rule=r1,
            defaults=dict(min_threshold=None, max_threshold=80.0, unit_override="kWh"),
        )
        ProductAlertRule.objects.update_or_create(
            product=p2, alert_rule=r4,
            defaults=dict(min_threshold=18.0, max_threshold=26.0, unit_override="°C"),
        )
        ProductAlertRule.objects.update_or_create(
            product=p3, alert_rule=r2,
            defaults=dict(min_threshold=None, max_threshold=5.0, unit_override="kWh"),
        )

        self.stdout.write(self.style.SUCCESS("Catálogo base cargado/actualizado correctamente."))
