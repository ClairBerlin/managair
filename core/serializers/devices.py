from rest_framework_json_api import serializers
from rest_framework_json_api.relations import HyperlinkedRelatedField

from core.models import (
    Quantity,
    NodeProtocol,
    NodeModel,
    Node,
    NodeFidelity,
    RoomNodeInstallation,
)


class QuantitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Quantity
        fields = ("quantity", "base_unit", "url")


class NodeProtocolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeProtocol
        fields = ("identifier", "num_uplink_msgs", "num_downlink_msgs", "url")


class NodeModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NodeModel
        fields = (
            "name",
            "trade_name",
            "manufacturer",
            "sensor_type",
            "quantities",
            "url",
        )


class NodeSerializer(serializers.HyperlinkedModelSerializer):
    related_serializers = {
        "installations": "core.serializers.RoomNodeInstallationSerializer",
        "samples": "SimpleSampleSerializer"
    }

    # A Node is installed in one or more rooms over its lifetime.
    installations = HyperlinkedRelatedField(
        many=True,
        read_only=False,
        allow_null=True,
        required=False,
        queryset=RoomNodeInstallation.objects.all(),
        self_link_view_name="node-relationships",
        related_link_view_name="node-related",
    )

    samples = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        allow_null=True,
        required=False,
        self_link_view_name="node-relationships",
        related_link_view_name="node-related"
    )

    class Meta:
        model = Node
        fields = (
            "id",
            "device_id",
            "alias",
            "protocol",
            "model",
            "installations",
            "samples",
            "url",
        )


class NodeFidelitySerializer(serializers.HyperlinkedModelSerializer):
    node = serializers.HyperlinkedRelatedField(
        view_name="node-detail", queryset=Node.objects.all()
    )

    class Meta:
        model = NodeFidelity
        fields = ("node", "fidelity", "last_contact_s", "last_check_s", "url")
