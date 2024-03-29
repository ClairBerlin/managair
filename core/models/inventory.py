import logging
from uuid import uuid4
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import ValidationError


logger = logging.getLogger(__name__)


def image_filename_to_uuid(instance, filename):
    extension = filename.split(".")[-1]
    return "{}.{}".format(uuid4(), extension)


class Organization(models.Model):
    """An Organization maintains an inventory of sensor nodes and sites where these nodes are installed."""

    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    users = models.ManyToManyField(
        User, through="Membership", related_name="organizations"
    )

    class Meta:
        constraints = [
            # Organiyations must have unique names.
            models.UniqueConstraint(
                fields=["name"], name="unique_org_name"
            )
        ]    
        ordering = ["name"]
        get_latest_by = "name"

    def get_owner(self):
        """The organization owns itself."""
        return self

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.name}"


class Membership(models.Model):
    """Models membership of a user in an organization"""

    OWNER = "O"
    INSPECTOR = "I"
    MEMBERSHIP_ROLE = [
        (OWNER, "User has full control of the organization and its inventory."),
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
        User, null=False, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, null=False, on_delete=models.CASCADE, related_name="memberships"
    )

    def __str__(self):
        """For representation in the Admin UI."""
        return f"{self.user.username} is member of {self.organization.name} with role {self.role}."

    def isOwner(self):
        """Return True if the membership role is OWNER."""
        return self.role == self.OWNER

    def get_owner(self):
        """Return the organization that is target of the present membership."""
        return self.organization

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
    # Default geolocation according to ISO 6709
    # positive values: north of the equator.
    latitude = models.DecimalField(
                max_digits=9, decimal_places=6, null=True, blank=True)
    # positive values: east of the Prime Meridian 
    longitude = models.DecimalField(
                max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
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

    def get_owner(self):
        """Return the organization that owns the present site."""
        return self.operator

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

    def get_owner(self):
        """Return the organization that owns the present room."""
        return self.site.operator

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
    # An ongoing association defaults to the maximum unix epoch, which is the maximum
    # 32-bit Integer, 2ˆ31 - 1 = 2147483647. This represents 2038-01-19T03:14:07.
    to_timestamp_s = models.PositiveIntegerField(blank=True, default=(2 ** 31 - 1))
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    image = models.ImageField(
        "Installation Photo", null=True, blank=True, upload_to=image_filename_to_uuid
    )

    class Meta:
        constraints = [
            # At any given time, a node may be installed in one room only.
            models.UniqueConstraint(
                fields=["node", "from_timestamp_s"], name="unique_node_installation"
            ),
        ]
        ordering = ["-from_timestamp_s"]
        get_latest_by = "from_timestamp_s"

    class JSONAPIMeta:
        resource_name = "Installation"

    def get_owner(self):
        """Return the organization that owns the present installation."""
        return self.room.site.operator

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()  # Ensure that our custom validation is run.
        super().save(force_insert, force_update, using, update_fields)

    def clean(self, *args, **kwargs):
        """Custom validation: Ensure that a node and room belong to the same owner."""
        node_owner = self.node.owner
        room_owner = self.room.site.operator
        logger.info(
            "Ensure that the installation of node %s in room %s is admissible.",
            self.node.id,
            self.room.id,
        )
        if node_owner != room_owner:
            raise ValidationError(
                "Room and Node of an Installation must have the same owner. "
            )
        super().clean(*args, **kwargs)

    def __str__(self):
        """For representation in the Admin UI."""
        end_time = (
            datetime.utcfromtimestamp(self.to_timestamp_s)
            if self.to_timestamp_s
            else "ongoing"
        )
        return f"Node: {self.node}, from: {datetime.utcfromtimestamp(self.from_timestamp_s)} To: {end_time}"

    def from_iso(self):
        return datetime.fromtimestamp(self.from_timestamp_s)

    def to_iso(self):
        return datetime.fromtimestamp(self.to_timestamp_s)