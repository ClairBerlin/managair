from datetime import datetime

from django.db import models

from .inventory import Organization


class Quantity(models.Model):
    quantity = models.CharField(max_length=30, blank=False, unique=True)
    base_unit = models.CharField(max_length=30, blank=False)

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.quantity}"


class NodeProtocol(models.Model):
    identifier = models.CharField(max_length=30, blank=False, unique=True)
    num_uplink_msgs = models.PositiveIntegerField(default=1)
    num_downlink_msgs = models.PositiveIntegerField(default=1)

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.identifier}"


class NodeModel(models.Model):
    name = models.CharField(max_length=30, blank=False, unique=True)
    trade_name = models.CharField(max_length=30)
    manufacturer = models.CharField(max_length=30, blank=False)
    sensor_type = models.CharField(max_length=100, blank=False)
    quantities = models.ManyToManyField(Quantity, related_name="node_models")

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.name}"


class Node(models.Model):
    id = models.UUIDField(primary_key=True)
    device_id = models.CharField(max_length=32, blank=False, unique=True)
    alias = models.CharField(max_length=100)
    protocol = models.ForeignKey(
        NodeProtocol, on_delete=models.CASCADE, related_name="nodes"
    )
    model = models.ForeignKey(
        NodeModel, null=False, on_delete=models.CASCADE, related_name="nodes"
    )
    owner = models.ForeignKey(
        Organization, null=False, on_delete=models.CASCADE, related_name="nodes"
    )

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.alias}: {self.id}"

    class Meta:
        ordering = ["device_id"]
        get_latest_by = "device_id"

    def check_fidelity(self, lookback_interval_s: int):
        """Check if a message was received within the lookback interval."""
        check_time_s = round(datetime.now().timestamp())
        fidelity = {"node": self, "last_check_s": check_time_s}
        latest_sample = self.samples.latest()
        if latest_sample is None:
            fidelity["fidelity"] = NodeFidelity.UNKNOWN
            fidelity["last_contact_s"] = None
        elif (check_time_s - latest_sample.timestamp_s) <= lookback_interval_s:
            fidelity["fidelity"] = NodeFidelity.ALIVE
            fidelity["last_contact_s"] = latest_sample.timestamp_s
        elif (check_time_s - latest_sample.timestamp_s) <= 2 * lookback_interval_s:
            fidelity["fidelity"] = NodeFidelity.MISSING
            fidelity["last_contact_s"] = latest_sample.timestamp_s
        else:
            fidelity["fidelity"] = NodeFidelity.DEAD
            fidelity["last_contact_s"] = latest_sample.timestamp_s
        return NodeFidelity.objects.update_or_create(
            node=fidelity["node"], defaults={**fidelity}
        )


class NodeFidelity(models.Model):
    """Maintain results of the node fidelity check."""

    UNKNOWN = "U"
    ALIVE = "E"
    MISSING = "M"
    DEAD = "D"
    FIDELITY_STATUS = [
        (UNKNOWN, "node has never reported data"),
        (ALIVE, "node did report data recently"),
        (MISSING, "node has not reported data recently"),
        (DEAD, "node has not reported data for some time"),
    ]
    node = models.OneToOneField(Node, on_delete=models.CASCADE, primary_key=True)
    fidelity = models.CharField(
        max_length=1, null=False, blank=False, choices=FIDELITY_STATUS, default=UNKNOWN
    )
    last_contact_s = models.PositiveIntegerField(null=True)
    last_check_s = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.node} --- Status: {self.fidelity}; Last seen: {datetime.fromtimestamp(self.last_contact_s)}; Last checked: {datetime.fromtimestamp(self.last_check_s)}"

    def last_contact_iso(self):
        return datetime.fromtimestamp(self.last_contact_s)

    def last_check_iso(self):
        return datetime.fromtimestamp(self.last_check_s)
