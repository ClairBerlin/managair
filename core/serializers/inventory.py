from core.models import Address, Membership, NodeInstallation, Organization, Site
from core.serializers import NodeSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

User = get_user_model()


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ("street1", "street2", "zip", "city", "url")


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {"address": AddressSerializer, "nodes": NodeSerializer}

    class Meta:
        model = Site
        fields = ("name", "description", "address", "nodes", "url")

    class JSONAPIMeta:
        included_resources = ["address"]


class NodeInstallationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {"node": NodeSerializer}

    class Meta:
        model = NodeInstallation
        fields = (
            "site",
            "node",
            "from_timestamp",
            "to_timestamp",
            "description",
            "url",
        )

    class JSONAPIMeta:
        included_resources = ["node"]


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

    memberships = serializers.ResourceRelatedField(
        source="users",
        read_only=True,
        many=True,
    )

    class Meta:
        model = Organization
        fields = ("name", "description", "memberships", "url")
