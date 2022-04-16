from datetime import datetime
import logging
from django.db import models

logger = logging.getLogger(__name__)


class StadpulsSensor(models.Model):
    installation = models.ForeignKey(
        "core.RoomNodeInstallation",
        null=False,
        on_delete=models.CASCADE,
        related_name="stadtpuls_sensor",
    )
    inserted_s = models.PositiveIntegerField(null=False, blank=False)
    stadtpuls_sensor_id = models.IntegerField(unique=True, null=False)

    def __str__(self):
        """String for representing the Model object."""
        return f"Installation ID: {self.installation}"

    def inserted_iso(self):
        return datetime.fromtimestamp(self.inserted_s)

    class Meta:
        ordering = ["stadtpuls_sensor_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["stadtpuls_sensor_id"], name="unique_statpuls_sensor")
        ]

