import logging

from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import (
    HyperlinkedRelatedField,
    ResourceRelatedField,
)

from core.models import (
    Address,
    Membership,
    Organization,
    Site,
    Room,
    Node,
    RoomNodeInstallation,
)
from core.serializers import SimpleSampleSerializer


logger = logging.getLogger(__name__)

User = get_user_model()


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ("street1", "street2", "zip", "city", "url", "latitude", "longitude")


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "address": "core.serializers.AddressSerializer",
        "operator": "core.serializers.OrganizationSerializer",
        "rooms": "core.serializers.RoomSerializer",
    }

    address = ResourceRelatedField(
        queryset=Address.objects.all(), related_link_view_name="site-related"
    )

    operator = ResourceRelatedField(
        queryset=Organization.objects.all(),
        related_link_url_kwarg="site_pk",
        related_link_view_name="site-related-organization",
    )

    #: A Site has zero or more room instances
    rooms = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Room.objects.all(),
        related_link_url_kwarg="site_pk",
        related_link_view_name="site-related-rooms",
    )

    class Meta:
        model = Site
        fields = ("name", "description", "address", "operator", "rooms", "url")

    class JSONAPIMeta:
        included_resources = ["address"]

    def get_owner(self):
        """Return the owner of the resource, once data is validated."""
        return self.validated_data["operator"]


class RoomNodeInstallationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "node": "core.serializers.NodeSerializer",
        "room": "core.serializers.RoomSerializer",
        # "timeseries": "core.serializers.TimeseriesSerializer",
    }

    node = ResourceRelatedField(
        queryset=Node.objects.all(),
        related_link_url_kwarg="installation_pk",
        related_link_view_name="installation-related-node",
    )

    room = ResourceRelatedField(
        queryset=Room.objects.all(), related_link_view_name="installation-related"
    )

    to_timestamp_s = serializers.IntegerField(required=False)
    # Image of the installation (optional). Handle upload in a separate serializer.
    image = serializers.ImageField(required=False, read_only=True)

    # Additional fields to merge the node installation with its samples.
    timeseries = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)
    query_timestamp_s = serializers.IntegerField(read_only=True)
    sample_count = serializers.IntegerField(read_only=True)
    latest_sample = SimpleSampleSerializer(many=False, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="installation-detail")

    class Meta:
        model = RoomNodeInstallation
        fields = [
            "room",
            "node",
            "timeseries",
            "query_timestamp_s",
            "from_timestamp_s",
            "to_timestamp_s",
            "sample_count",
            "latest_sample",
            "description",
            "image",
            "is_public",
            "url",
        ]

    def __init__(self, *args, **kwargs):
        # Don't pass the "include_timeseries" arg up to the superclass
        include_timeseries = kwargs.pop("include_timeseries", None)
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if not include_timeseries:
            self.fields.pop("timeseries")

    def get_owner(self):
        """Return the owner of the resource, once data is validated."""
        room = self.validated_data["room"]
        site = room.site
        owner = site.operator
        return owner

    def validate(self, attrs):
        """
        Ensure that the node is owned by the same organization as the room.
        """
        logger.debug(
            "For a new or updated installation, validate that node and room belong to the same owner."
        )
        siteOperator = attrs["room"].site.operator if "room" in attrs else None
        nodeOwner = attrs["node"].owner if "node" in attrs else None

        if siteOperator != nodeOwner:
            raise serializers.ValidationError(
                "In an installation, node and room must belong to the same owner."
            )
        return attrs


class InstallationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomNodeInstallation
        fields = ["image"]


class RoomSerializer(serializers.HyperlinkedModelSerializer):
    related_serializers = {
        "site": "core.serializers.SiteSerializer",
        "installations": "core.serializers.RoomNodeInstallationSerializer",
    }

    site = ResourceRelatedField(
        queryset=Site.objects.all(),
        related_link_url_kwarg="room_pk",
        related_link_view_name="room-related-site",
    )

    #: A Room contains zero or more node installations.
    installations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=RoomNodeInstallation.objects.all(),
        related_link_url_kwarg="room_pk",
        related_link_view_name="room-related-installations",
    )

    class Meta:
        model = Room

        fields = [
            "name",
            "description",
            "size_sqm",
            "height_m",
            "max_occupancy",
            "site",
            "installations",
            "url",
        ]

    def get_owner(self):
        """Return the owner of the resource, once data is validated."""
        site = self.validated_data["site"]
        owner = site.operator
        return owner


class MembershipSerializer(serializers.ModelSerializer):
    included_serializers = {
        "organization": "core.serializers.OrganizationSerializer",
        "user": "core.serializers.UserSerializer",
    }

    user_name = serializers.ReadOnlyField(source="user.username")
    organization_name = serializers.ReadOnlyField(source="organization.name")

    organization = ResourceRelatedField(
        allow_null=False,
        required=True,
        queryset=Organization.objects.all(),
        related_link_view_name="membership-related",
    )

    user = ResourceRelatedField(
        allow_null=False,
        required=True,
        queryset=User.objects.all(),
        related_link_view_name="membership-related",
    )

    class Meta:
        model = Membership
        fields = (
            "organization",
            "user",
            "user_name",
            "organization_name",
            "role",
            "url",
        )

    def get_owner(self):
        """Return the owner of the resource, once data is validated."""
        return self.validated_data["organization"]


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "users": "core.serializers.UserSerializer",
        "memberships": "core.serializers.MembershipSerializer",
        "sites": "core.serializers.SiteSerializer",
        "nodes": "core.serializers.NodeSerializer",
    }
    # An Organization has one or more users as members.
    users = ResourceRelatedField(
        many=True,
        allow_null=True,
        required=False,
        queryset=User.objects.all(),
        related_link_url_kwarg="organization_pk",
        related_link_view_name="organization-related-users",
    )
    # An Organization operates zero or more sites.
    sites = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Memberships cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_url_kwarg="organization_pk",
        related_link_view_name="organization-related-sites",
    )
    # An Organization is related to its members via Memberships.
    memberships = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Sites cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_url_kwarg="organization_pk",
        related_link_view_name="organization-related-memberships",
    )
    # An Organization operates one or more nodes.
    nodes = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Nodes cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_url_kwarg="organization_pk",
        related_link_view_name="organization-related-nodes",
    )

    class Meta:
        model = Organization
        fields = (
            "name",
            "description",
            "users",
            "memberships",
            "sites",
            "nodes",
            "url",
        )


class UsernameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["username", "url"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "organizations": "core.serializers.OrganizationSerializer",
        "memberships": "core.serializers.MembershipSerializer",
    }
    # A User is member of zero or more organizations.
    organizations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Organization.objects.all(),
        self_link_view_name="user-relationships",
        related_link_view_name="user-related",
    )
    # A User holds zero or more organization memberships.
    memberships = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Memberships cannot be detached from their user.
        allow_null=True,
        required=False,
        related_link_view_name="user-related",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "organizations",
            "memberships",
            "url",
        )
