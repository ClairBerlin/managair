from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class Organization(models.Model):
    """An Organization maintains an inventory of sensor nodes and sites where these nodes are installed."""

    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    users = models.ManyToManyField(
        User, through="Membership", related_name="organizations"
    )

    class Meta:
        ordering = ["name"]
        get_latest_by = "name"

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.name}"


class Membership(models.Model):
    """Models membership of a user in an organization"""

    OWNER = "O"
    ASSISTANT = "A"
    INSPECTOR = "I"
    MEMBERSHIP_ROLE = [
        (OWNER, "User has full control of the organization and its inventory."),
        (ASSISTANT, "User can perform a restricted set of tasks in the organization."),
        (INSPECTOR, "User can inspect the organization's inventory."),
    ]
    role = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=MEMBERSHIP_ROLE,
        default=INSPECTOR,
    )
    user = models.ForeignKey(
        User,
        null=False,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization,
        null=False,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.user.username} is member of {self.organization.name} with role {self.role}."

    class Meta:
        constraints = [
            # Memberships must be unique.
            models.UniqueConstraint(
                fields=["user", "organization"], name="unique-membership"
            ),
        ]
        ordering = ["role", "organization"]


class Address(models.Model):
    street1 = models.CharField(max_length=50, null=False, blank=False)
    street2 = models.CharField(max_length=50, null=True, blank=True)
    zip = models.CharField(max_length=5, null=False, blank=False)
    city = models.CharField(max_length=50, null=False, blank=False)
    # TODO: Add geolocation.

    class Meta:
        constraints = [
            # Addresses must be unique, but local differentiation is admissible.
            models.UniqueConstraint(
                fields=["street1", "street2", "zip", "city"], name="unique_address"
            )
        ]
        ordering = ["city", "street1"]
        get_latest_by = "city"

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.street1}, {self.zip} {self.city}"


class Site(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="sites")
    operator = models.ForeignKey(
        Organization, null=False, on_delete=models.CASCADE, related_name="sites"
    )

    class Meta:
        constraints = [
            # The sites of a given organization must be unique.
            models.UniqueConstraint(
                fields=["name", "operator"], name="unique_site_per_organization"
            )
        ]
        ordering = ["name"]
        get_latest_by = "name"

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.name} {self.address.street1}, {self.address.zip}"


class Room(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    size_sqm = models.DecimalField(max_digits=5, decimal_places=1, null=True)
    height_m = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    max_occupancy = models.IntegerField(null=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="rooms")
    nodes = models.ManyToManyField(
        "core.Node", through="RoomNodeInstallation", related_name="rooms"
    )

    class Meta:
        constraints = [
            # The rooms within a given site must be unique.
            models.UniqueConstraint(
                fields=["name", "site"], name="unique_room_per_site"
            )
        ]
        ordering = ["name"]
        get_latest_by = "name"

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.name}"


class RoomNodeInstallation(models.Model):
    node = models.ForeignKey(
        "core.Node", null=False, on_delete=models.CASCADE, related_name="installations"
    )
    room = models.ForeignKey(
        Room, null=False, on_delete=models.CASCADE, related_name="installations"
    )
    from_timestamp_s = models.PositiveIntegerField(null=False, blank=False)
    # An ongoing association does not have an end-timestamp set.
    to_timestamp_s = models.PositiveIntegerField(null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            # At any given time, a node may be installed in one room only.
            models.UniqueConstraint(
                fields=["node", "from_timestamp_s"], name="unique_node_installation"
            ),
        ]
        ordering = ["-from_timestamp_s"]
        get_latest_by = "from_timestamp_s"

    def __str__(self):
        """For representation in the Admin UI."""
        end_time = (
            datetime.utcfromtimestamp(self.to_timestamp_s)
            if self.to_timestamp_s is not None
            else "ongoing"
        )
        return f"Node: {self.node}, from: {datetime.utcfromtimestamp(self.from_timestamp_s)} To: {end_time}"

    def from_iso(self):
        return datetime.fromtimestamp(self.from_timestamp_s)

    def to_iso(self):
        return datetime.fromtimestamp(self.to_timestamp_s)