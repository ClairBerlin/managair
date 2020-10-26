from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class Organization(models.Model):
    """An Organization maintains an inventory of sensor nodes and sites where these nodes are installed."""

    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    users = models.ManyToManyField(User, through="Membership")

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
        related_name="organization_membership",
    )
    organization = models.ForeignKey(
        Organization,
        null=False,
        on_delete=models.CASCADE,
        related_name="user_membership",
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

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.street1}, {self.zip} {self.city}"


class Site(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="sites")
    operated_by = models.ForeignKey(
        Organization, null=False, on_delete=models.CASCADE, related_name="sites"
    )

    class Meta:
        constraints = [
            # The sites of a given organization must be unique.
            models.UniqueConstraint(
                fields=["name", "operated_by"], name="unique_site_per_organization"
            )
        ]

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
    nodes = models.ManyToManyField("core.Node", through="RoomNodeInstallation")

    class Meta:
        constraints = [
            # The rooms within a given site must be unique.
            models.UniqueConstraint(
                fields=["name", "site"], name="unique_room_per_site"
            )
        ]

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.name}"


class RoomNodeInstallation(models.Model):
    node = models.ForeignKey(
        "core.Node",
        null=False,
        on_delete=models.CASCADE,
        related_name="room_installation",
    )
    room = models.ForeignKey(
        Room, null=False, on_delete=models.CASCADE, related_name="node_installations"
    )
    from_timestamp = models.PositiveIntegerField(null=False, blank=False)
    # An ongoing association does not have an end timestamp set.
    to_timestamp = models.PositiveIntegerField(null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            # At any given time, a node may be installed in one room only.
            models.UniqueConstraint(
                fields=["node", "from_timestamp"], name="unique_node_installation"
            ),
        ]
        ordering = ["-from_timestamp"]
        get_latest_by = "from_timestamp"

    def __str__(self):
        """For representation in the Admin UI."""
        end_time = (
            datetime.utcfromtimestamp(self.to_timestamp)
            if self.to_timestamp is not None
            else "ongoing"
        )
        return f"Node: {self.node}, from: {datetime.utcfromtimestamp(self.from_timestamp)} To: {end_time}"

    def from_iso(self):
        return datetime.fromtimestamp(self.from_timestamp)

    def to_iso(self):
        return datetime.fromtimestamp(self.to_timestamp)