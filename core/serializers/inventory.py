from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from dj_rest_auth.serializers import UserDetailsSerializer

from django.contrib.auth.models import User

from core.models import Address, NodeInstallation, Site, Organization, \
    Membership
from core.serializers import NodeSerializer

class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = ('street1', 'street2', 'zip', 'city', 'url')


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        'address': AddressSerializer,
        'nodes': NodeSerializer
        }
    
    class Meta:
        model = Site
        fields = ('name', 'description', 'address', 'nodes', 'url')

    class JSONAPIMeta:
        included_resources = ['address']


class NodeInstallationSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        'node': NodeSerializer
        }
    
    class Meta:
        model = NodeInstallation
        fields = ('site', 'node', 'from_timestamp', 'to_timestamp', 'description', 'url')

    class JSONAPIMeta:
        included_resources = ['node']


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organization
        fields = ('name', 'description', 'url')


class MembershipSerializer(serializers.HyperlinkedModelSerializer):
    included_serializers = {
        'organization': OrganizationSerializer,
    }

    user = UserDetailsSerializer()
    # TODO: Add user hyperlinks.

    class Meta:
        model = Membership
        fields = ('organization', 'user', 'url')
    
    class JSONAPIMeta:
        included_resources = ['organization', 'user']
