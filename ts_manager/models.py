from django.db import models
from django.db.models import Q
from enum import Enum, unique
from device_manager.models import Node
from datetime import datetime


class Sample(models.Model):
    MEASUREMENT = 'M'
    REPLACEMENT = 'R'
    ERROR = 'E'
    MEASUREMENT_STATUS = [
        (MEASUREMENT, 'measured value'),
        (REPLACEMENT, 'replacement value'),
        (ERROR, 'measurement error')
    ]

    node_ref = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='samples')
    timestamp_s = models.PositiveIntegerField(null=False, blank=False)
    co2_ppm = models.PositiveSmallIntegerField(null=False, blank=False)
    temperature_celsius = models.DecimalField(
        null=True,
        decimal_places=1,
        max_digits=3)
    rel_humidity_percent = models.PositiveSmallIntegerField(null=True)
    measurement_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=MEASUREMENT_STATUS,
        default=MEASUREMENT_STATUS)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['node_ref', 'timestamp_s'],
                name='unique_sampling_times_per_node'),
            models.CheckConstraint(
                check=Q(rel_humidity__lte=100),
                name='rel_humidity_percent'),
            models.CheckConstraint(
                check=Q(temperature_celsius__gte=-20),
                name='not_too_cold'
            ),
            models.CheckConstraint(
                check=Q(temperature_celsius__lte=40),
                name='not_too_hot'
            ),
            models.CheckConstraint(
            check = Q(co2_ppm__lte=10000),
                name = 'co2_upper_limit'
            )
        ]
        ordering = ['-timestamp_s']
        get_latest_by = 'order_timestamp_s'
