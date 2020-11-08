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

User = get_user_model()


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ("street1", "street2", "zip", "city", "url")


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "address": "core.serializers.AddressSerializer",
        "operated_by": "core.serializers.OrganizationSerializer",
        "rooms": "core.serializers.RoomSerializer",
    }

    address = ResourceRelatedField(
        queryset=Address.objects.all(), related_link_view_name="site-related"
    )

    operated_by = ResourceRelatedField(
        queryset=Organization.objects.all(), related_link_view_name="site-related"
    )

    #: A Site has zero or more room instances
    rooms = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Room.objects.all(),
        related_link_view_name="site-related",
    )

    class Meta:
        model = Site
        fields = ("name", "description", "address", "operated_by", "rooms", "url")

    class JSONAPIMeta:
        included_resources = ["address"]


class RoomNodeInstallationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "node": "core.serializers.NodeSerializer",
        "room": "core.serializers.RoomSerializer",
    }

    node = ResourceRelatedField(
        queryset=Node.objects.all(), related_link_view_name="installation-related"
    )

    room = ResourceRelatedField(
        queryset=Room.objects.all(), related_link_view_name="installation-related"
    )

    url = serializers.HyperlinkedIdentityField(
        view_name='installation-detail'
    )

    class Meta:
        model = RoomNodeInstallation
        fields = [
            "room",
            "node",
            "from_timestamp_s",
            "to_timestamp_s",
            "description",
            "url",
        ]


class RoomSerializer(serializers.HyperlinkedModelSerializer):
    related_serializers = {
        "site": "core.serializers.SiteSerializer",
        "installations": "core.serializers.RoomNodeInstallationSerializer",
    }

    site = ResourceRelatedField(
        queryset=Site.objects.all(), related_link_view_name="room-related"
    )

    #: A Room contains zero or more node installations.
    installations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=RoomNodeInstallation.objects.all(),
        related_link_view_name="room-related",
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
        self_link_view_name="organization-relationships",
        related_link_view_name="organization-related",
    )
    # An Organization is related to its members via Memberships.
    sites = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Memberships cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_view_name="organization-related",
    )
    # An Organization operates zero or more sites.
    memberships = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Sites cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_view_name="organization-related",
    )
    # An Organization operates one or more nodes.
    nodes = HyperlinkedRelatedField(
        many=True,
        read_only=True,  # Nodes cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_view_name="organization-related",
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
