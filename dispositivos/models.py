# dispositivos/models.py
from django.db import models
from django.db.models import Q, F
from organizations.models import Organization


# ──────────────────────────────────────────────────────────────────────────────
# BaseModel (abstracta con trazabilidad y “borrado lógico”)
# ──────────────────────────────────────────────────────────────────────────────
class BaseModel(models.Model):
    STATUS_CHOICES = [("ACTIVE", "Activo"), ("INACTIVE", "Inactivo")]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        help_text="Estado lógico del registro.",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Creación")
    updated_at = models.DateTimeField(auto_now=True, help_text="Última actualización")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Borrado lógico")

    class Meta:
        abstract = True


# ──────────────────────────────────────────────────────────────────────────────
# Maestros globales: Category, Product, AlertRule, ProductAlertRule
# ──────────────────────────────────────────────────────────────────────────────
class Category(BaseModel):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "category"
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=160)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,   # evita borrar categorías con productos asociados
        related_name="products",
    )
    sku = models.CharField(max_length=80, unique=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    nominal_voltage_v = models.FloatField(null=True, blank=True)
    max_current_a = models.FloatField(null=True, blank=True)
    standby_power_w = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "product"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["sku"]),
        ]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


class AlertRule(BaseModel):
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    name = models.CharField(max_length=140)
    severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.MEDIUM
    )
    unit = models.CharField(max_length=32, default="kWh")

    # Umbrales por defecto (opcionales)
    default_min_threshold = models.FloatField(null=True, blank=True)
    default_max_threshold = models.FloatField(null=True, blank=True)

    # Relación N:M con datos extra en la tabla intermedia
    products = models.ManyToManyField(
        "Product",
        through="ProductAlertRule",
        related_name="alert_rules",
        blank=True,
    )

    class Meta:
        db_table = "alert_rule"
        indexes = [
            models.Index(fields=["severity"]),
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(default_min_threshold__isnull=True)
                | Q(default_max_threshold__isnull=True)
                | Q(default_min_threshold__lte=F("default_max_threshold")),
                name="alert_rule_default_min_lte_max",
            )
        ]
        unique_together = [("name", "severity")]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} [{self.severity}]"

    def effective_thresholds_for(self, product):
        """
        Devuelve (min, max) efectivos para un producto:
        primero busca override en ProductAlertRule; si no, usa los defaults.
        """
        link = ProductAlertRule.objects.filter(
            product=product, alert_rule=self
        ).first()
        if link and link.min_threshold is not None and link.max_threshold is not None:
            return link.min_threshold, link.max_threshold
        return self.default_min_threshold, self.default_max_threshold


class ProductAlertRule(BaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_alert_links"
    )
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE, related_name="product_alert_links"
    )
    min_threshold = models.FloatField(null=True, blank=True)
    max_threshold = models.FloatField(null=True, blank=True)
    unit_override = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = "product_alert_rule"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "alert_rule"], name="uix_product_alert_unique"
            ),
            models.CheckConstraint(
                check=Q(min_threshold__isnull=True)
                | Q(max_threshold__isnull=True)
                | Q(min_threshold__lte=F("max_threshold")),
                name="par_min_lte_max",
            ),
        ]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["alert_rule"]),
            models.Index(fields=["product", "alert_rule"]),
        ]
        ordering = ["product_id", "alert_rule_id"]

    def __str__(self) -> str:
        return f"{self.product.name} ⟷ {self.alert_rule.name}"


# ──────────────────────────────────────────────────────────────────────────────
# Datos por organización (tenant): Zone, Device, Measurement, AlertEvent
# ──────────────────────────────────────────────────────────────────────────────
class Zone(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="zones"
    )
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "zone"
        unique_together = [("organization", "name")]
        ordering = ["organization_id", "name"]
        verbose_name = "Zone"
        verbose_name_plural = "Zones"

    def __str__(self) -> str:
        return f"{self.name} @ {self.organization.name}"


class Device(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="devices"
    )
    zone = models.ForeignKey(
        Zone, on_delete=models.PROTECT, related_name="devices"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="devices"
    )

    name = models.CharField(
        max_length=160, help_text="Nombre único dentro de la organización."
    )
    max_power_w = models.PositiveIntegerField()
    image = models.ImageField(upload_to="devices/", null=True, blank=True)
    serial_number = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "device"
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["zone"]),
            models.Index(fields=["product"]),
        ]
        unique_together = [("organization", "name")]
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self) -> str:
        return f"{self.name} @ {self.organization.name}"


class Measurement(BaseModel):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="measurements"
    )
    measured_at = models.DateTimeField(auto_now_add=True)
    energy_kwh = models.FloatField()

    triggered_alert = models.ForeignKey(
        AlertRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_measurements",
    )

    class Meta:
        db_table = "measurement"
        indexes = [
            models.Index(fields=["device", "measured_at"]),
            models.Index(fields=["triggered_alert"]),
        ]
        ordering = ["-measured_at"]
        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"

    def __str__(self) -> str:
        return f"{self.device} - {self.energy_kwh} kWh @ {self.measured_at:%Y-%m-%d %H:%M}"


class AlertEvent(BaseModel):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="alert_events"
    )
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.PROTECT, related_name="alert_events"
    )
    occurred_at = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=240, blank=True)

    class Meta:
        db_table = "alert_event"
        indexes = [
            models.Index(fields=["device", "occurred_at"]),
            models.Index(fields=["alert_rule"]),
        ]
        ordering = ["-occurred_at"]
        verbose_name = "Alert Event"
        verbose_name_plural = "Alert Events"

    def __str__(self) -> str:
        return f"[{self.alert_rule.severity}] {self.alert_rule.name} @ {self.device}"
