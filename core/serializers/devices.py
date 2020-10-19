from rest_framework_json_api import serializers

from core.models import Quantity, NodeProtocol, NodeModel, Node, NodeFidelity

class QuantitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Quantity
        fields = ('quantity', 'base_unit', 'url')

class NodeProtocolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeProtocol
        fields = ('identifier', 'num_uplink_msgs', 'num_downlink_msgs','url')

class NodeModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeModel
        fields = ('name', 'trade_name', 'manufacturer', 'sensor_type', 'quantities', 'url')

class NodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Node
        fields = ('id', 'device_id', 'alias', 'protocol', 'model', 'url')

class NodeFidelitySerializer(serializers.HyperlinkedModelSerializer):
    node = serializers.HyperlinkedRelatedField(
        view_name='node-detail', queryset=Node.objects.all())

    class Meta:
        model = NodeFidelity
        fields = ('node', 'fidelity', 'last_contact_s', 'last_check_s', 'url')
