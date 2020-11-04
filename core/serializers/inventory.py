from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import HyperlinkedRelatedField

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
        "address": AddressSerializer,
        "rooms": "core.serializers.RoomSerializer",
    }

    #: A Site has zero or more room instances
    rooms = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Room.objects.all(),
        self_link_view_name="site-relationships",
        related_link_view_name="site-related",
    )

    class Meta:
        model = Site
        fields = ("name", "description", "address", "rooms", "url")

    class JSONAPIMeta:
        included_resources = ["address"]


class RoomNodeInstallationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "room": "core.serializers.RoomSerializer",
        "node": "core.serializers.NodeSerializer",
    }
    
    class Meta:
        model = RoomNodeInstallation
        fields = ["room", "node", "from_timestamp_s", "to_timestamp_s", "description"]



class RoomSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "installations": "core.serializers.RoomNodeInstallationSerializer",
    }

    #: A Room contains zero or more node installations. 
    installations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=RoomNodeInstallation.objects.all(),
        self_link_view_name="room-relationships",
        related_link_view_name="room-related",
    )

    class Meta:
        model = Room
        fields = ["name", "description", "site", "nodes", "installations", "url"]



class MembershipSerializer(serializers.HyperlinkedModelSerializer):

    user_id = serializers.ReadOnlyField(source="user.id")
    user_name = serializers.ReadOnlyField(source="user.username")
    organization_id = serializers.ReadOnlyField(source="organization.id")
    organization_name = serializers.ReadOnlyField(source="organization.name")

    class Meta:
        model = Membership
        fields = (
            "organization",
            "user_id",
            "user_name",
            "organization_id",
            "organization_name",
            "role",
            "url",
        )


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "users": "core.serializers.UserSerializer",
        "sites": "core.serializers.SiteSerializer",
        "nodes": "core.serializers.NodeSerializer",
    }
    # An Organization has one or more users as members.
    users = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=User.objects.all(),
        self_link_view_name="organization-relationships",
        related_link_view_name="organization-related",
    )
    # An Organization operates zero or more sites.
    sites = HyperlinkedRelatedField(
        many=True,
        read_only=True, # Sites cannot be detached from their organization.
        allow_null=True,
        required=False,
        related_link_view_name="organization-related",
    )
    # An Organization operates one or more nodes.
    nodes = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Node.objects.all(),
        related_link_view_name="organization-related",
    )

    class Meta:
        model = Organization
        fields = ("name", "description", "users", "sites", "nodes", "url")


class UserSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        "organizations": "core.serializers.OrganizationSerializer",
    }
    #: A User is member of zero or more organizations.
    organizations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=Organization.objects.all(),
        self_link_view_name="user-relationships",
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
            "url",
        )
