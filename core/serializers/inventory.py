from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from core.models import (
    Address,
    Membership,
    Organization,
    Site,
    Room,
)

User = get_user_model()


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ("street1", "street2", "zip", "city", "url")


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {"address": AddressSerializer}
    related_serializers = {
        "rooms": "core.serializers.RoomSerializer",
    }

    #: A Site has zero or more room instances
    rooms = ResourceRelatedField(
        model=Room,
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
        fields = ("name", "description", "address", "rooms", "nodes", "url")

    class JSONAPIMeta:
        included_resources = ["address"]


class RoomSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Room
        fields = ["name", "description", "site", "url"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "url",
        )


class MembershipSerializer(serializers.HyperlinkedModelSerializer):

    user_id = serializers.ReadOnlyField(source="user.id")
    user_name = serializers.ReadOnlyField(source="user.username")
    organization_id = serializers.ReadOnlyField(source="organization.id")
    organization_name = serializers.ReadOnlyField(source="organization.name")
    user = UserSerializer

    class Meta:
        model = Membership
        fields = (
            "organization",
            "user",
            "user_id",
            "user_name",
            "organization_id",
            "organization_name",
            "role",
            "url",
        )


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):

    users = ResourceRelatedField(
        many=True,
        read_only=True,
        related_link_view_name="user-detail",
    )

    class Meta:
        model = Organization
        fields = ("name", "description", "users", "url")
