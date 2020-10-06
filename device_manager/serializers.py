from rest_framework_json_api import serializers
from device_manager.models import Quantity, NodeProtocol, NodeModel, Node

class NodeProtocolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeProtocol
        fields = ('identifier', 'num_uplink_msgs', 'num_downlink_msgs', 'url')

class NodeModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeModel
        fields = ('name', 'trade_name', 'manufacturer', 'sensor_type', 'url')

class NodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Node
        fields = ('id', 'device_id', 'alias', 'protocol', 'model', 'url')