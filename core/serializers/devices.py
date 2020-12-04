from rest_framework_json_api import serializers
from rest_framework_json_api.relations import (
    HyperlinkedRelatedField,
    ResourceRelatedField,
)

from core.models import (
    Quantity,
    NodeProtocol,
    NodeModel,
    Node,
    NodeFidelity,
    Organization,
)
from core.serializers import SimpleSampleSerializer


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
        "protocol": "core.serializers.NodeProtocolSerializer",
        "model": "core.serializers.NodeModelSerializer",
        "owner": "core.serializers.OrganizationSerializer",
        "installations": "core.serializers.RoomNodeInstallationSerializer",
    }

    protocol = ResourceRelatedField(
        queryset=NodeProtocol.objects.all(), related_link_view_name="node-related"
    )

    model = ResourceRelatedField(
        queryset=NodeModel.objects.all(), related_link_view_name="node-related"
    )

    owner = ResourceRelatedField(
        queryset=Organization.objects.all(), related_link_view_name="node-related"
    )

    # A Node is installed in one or more rooms over its lifetime.
    installations = HyperlinkedRelatedField(
        many=True,
        read_only=True,
        related_link_view_name="node-related",
    )

    # Additional fields to merge the node model with its samples.
    timeseries = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)
    query_timestamp_s = serializers.IntegerField(read_only=True)
    sample_count = serializers.IntegerField(read_only=True)
    from_timestamp_s = serializers.IntegerField(read_only=True)
    to_timestamp_s = serializers.IntegerField(read_only=True)

    class Meta:
        model = Node
        fields = (
            "id",
            "eui64",
            "alias",
            "description",
            "query_timestamp_s",
            "from_timestamp_s",
            "to_timestamp_s",
            "sample_count",
            "timeseries",
            "protocol",
            "model",
            "owner",
            "installations",
            "url",
        )

    def __init__(self, *args, **kwargs):
        # Don't pass the "include_timeseries" arg up to the superclass
        include_timeseries = kwargs.pop("include_timeseries", None)
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if not include_timeseries:
            self.fields.pop("timeseries")

    def get_owner(self):
        """Return the owner of the resource, once data is validated."""
        return self.validated_data["owner"]


class NodeFidelitySerializer(serializers.HyperlinkedModelSerializer):
    node = serializers.HyperlinkedRelatedField(
        view_name="node-detail", queryset=Node.objects.all()
    )

    class Meta:
        model = NodeFidelity
        fields = ("node", "fidelity", "last_contact_s", "last_check_s", "url")
