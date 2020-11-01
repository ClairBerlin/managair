from datetime import datetime

from django.db import models
from django.db.models import Q

from .devices import Node


class Sample(models.Model):
    MEASUREMENT = "M"
    REPLACEMENT = "R"
    ERROR = "E"
    MEASUREMENT_STATUS = [
        (MEASUREMENT, "measured value"),
        (REPLACEMENT, "replacement value"),
        (ERROR, "measurement error"),
    ]

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="samples")
    timestamp_s = models.PositiveIntegerField(null=False, blank=False)
    co2_ppm = models.PositiveSmallIntegerField(null=False, blank=False)
    temperature_celsius = models.DecimalField(null=True, decimal_places=1, max_digits=3)
    rel_humidity_percent = models.PositiveSmallIntegerField(null=True)
    measurement_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=MEASUREMENT_STATUS,
        default=MEASUREMENT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["node", "timestamp_s"], name="unique_sampling_times_per_node"
            ),
            models.CheckConstraint(
                check=Q(rel_humidity_percent__lte=100), name="rel_humidity_percent"
            ),
            models.CheckConstraint(
                check=Q(temperature_celsius__gte=-20), name="not_too_cold"
            ),
            models.CheckConstraint(
                check=Q(temperature_celsius__lte=40), name="not_too_hot"
            ),
            models.CheckConstraint(check=Q(co2_ppm__lte=10000), name="co2_upper_limit"),
        ]
        ordering = ["timestamp_s"]
        get_latest_by = "timestamp_s"

    def timestamp_iso(self):
        return datetime.fromtimestamp(self.timestamp_s)
