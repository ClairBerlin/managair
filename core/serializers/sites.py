from rest_framework_json_api import serializers
from core.models import Address, NodeInstallation, Site
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