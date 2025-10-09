from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import random

from dispositivos.models import (
    Device, Measurement, AlertEvent, AlertRule, ProductAlertRule
)

class Command(BaseCommand):
    help = "Genera mediciones de ejemplo (últimos días) y crea AlertEvent simulados según umbrales."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        devices = list(Device.objects.select_related("product", "organization"))
        if not devices:
            self.stdout.write(self.style.WARNING("No hay dispositivos. Corre antes: seed_catalog_es y seed_demo_org_es"))
            return

        # Reglas conocidas (si no existen, seed_catalog_es no se corrió)
        rules_by_name = {r.name: r for r in AlertRule.objects.all()}

        # Helper para umbrales efectivos por producto
        def effective_thresholds(alert_rule, product):
            # override en ProductAlertRule si existe, si no, defaults de la regla
            link = ProductAlertRule.objects.filter(product=product, alert_rule=alert_rule).first()
            min_t = link.min_threshold if (link and link.min_threshold is not None) else alert_rule.default_min_threshold
            max_t = link.max_threshold if (link and link.max_threshold is not None) else alert_rule.default_max_threshold
            return (min_t, max_t)

        created_measurements = 0
        created_alerts = 0

        # Para cada device creamos ~60 mediciones en los últimos 3 días (una por ~hora y media)
        for d in devices:
            base = random.uniform(0.2, 2.5)  # base kWh “normal” para el demo
            t = now - timedelta(days=3)
            points = []

            while t < now:
                # Variar consumo con “ruido”
                value = max(0.0, base + random.uniform(-0.2, 0.8))
                points.append((t, value))
                t += timedelta(minutes=90)

            # Persistimos (en bloques para mejor perf en BD reales)
            m_objs = [
                Measurement(
                    device=d,
                    energy_kwh=value,
                    measured_at=ts,
                )
                for (ts, value) in points
            ]
            Measurement.objects.bulk_create(m_objs, batch_size=200)
            created_measurements += len(m_objs)

            # Evaluar alertas para las últimas N mediciones (no todas para ser liviano)
            last_ms = Measurement.objects.filter(device=d).order_by("-measured_at")[:20]
            product = d.product

            # Simular alto consumo si se supera umbral efectivo de "Consumo alto"
            r_high = rules_by_name.get("Consumo alto")
            if r_high:
                mn, mx = effective_thresholds(r_high, product)
                if mx is not None:
                    for m in last_ms:
                        if m.energy_kwh > mx:
                            AlertEvent.objects.create(
                                device=d,
                                alert_rule=r_high,
                                occurred_at=m.measured_at,
                                message=f"Consumo {m.energy_kwh:.2f} kWh supera umbral {mx:.2f} kWh",
                            )
                            created_alerts += 1

            # Simular bajo rendimiento si cae por debajo de umbral
            r_low = rules_by_name.get("Bajo rendimiento")
            if r_low:
                mn, mx = effective_thresholds(r_low, product)
                if mn is not None:
                    for m in last_ms:
                        if m.energy_kwh < mn:
                            AlertEvent.objects.create(
                                device=d,
                                alert_rule=r_low,
                                occurred_at=m.measured_at,
                                message=f"Rendimiento {m.energy_kwh:.2f} kWh inferior a {mn:.2f} kWh",
                            )
                            created_alerts += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK: {created_measurements} mediciones y {created_alerts} alertas simuladas creadas."
        ))
