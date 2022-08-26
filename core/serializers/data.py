from rest_framework_json_api import serializers

from core.data_viewmodels import (
    NodeTimeseriesListViewModel,
    NodeTimeseriesViewModel,
    InstallationTimeseriesListViewModel,
    InstallationTimeseriesViewModel,
    RoomAirQualityViewModel,
)
from core.models import Sample


class SimpleSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        exclude = ["node"]


class NodeTimeseriesListSerializer(serializers.Serializer):
    node_alias = serializers.CharField(max_length=100)
    query_timestamp_s = serializers.IntegerField()
    from_timestamp_s = serializers.IntegerField()
    to_timestamp_s = serializers.IntegerField()
    sample_count = serializers.IntegerField()

    url = serializers.HyperlinkedIdentityField(view_name="node-timeseries-detail")

    class Meta:
        model = NodeTimeseriesListViewModel
        fields = ["url"]

    class JSONAPIMeta:
        resource_name = "Node-Timeseries"


class NodeTimeseriesSerializer(NodeTimeseriesListSerializer):
    samples = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)

    class Meta:
        model = NodeTimeseriesViewModel
        fields = ["url"]

    class JSONAPIMeta:
        resource_name = "Node-Timeseries"


class InstallationTimeseriesListSerializer(serializers.Serializer):
    node_id = serializers.CharField()
    node_alias = serializers.CharField(max_length=100)
    query_timestamp_s = serializers.IntegerField()
    from_timestamp_s = serializers.IntegerField()
    to_timestamp_s = serializers.IntegerField()
    sample_count = serializers.IntegerField()

    url = serializers.HyperlinkedIdentityField(
        view_name="installation-timeseries-detail"
    )

    class Meta:
        model = InstallationTimeseriesListViewModel
        fields = ["url"]

    class JSONAPIMeta:
        resource_name = "Installation-Timeseries"


class InstallationTimeSeriesSerializer(InstallationTimeseriesListSerializer):
    samples = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)

    class Meta:
        model = InstallationTimeseriesViewModel
        fields = ["url"]

    class JSONAPIMeta:
        resource_name = "Installation-Timeseries"

class RoomAirQualitySerializer(serializers.Serializer):
    analysis_month = serializers.CharField(read_only=True)
    query_timestamp_s = serializers.IntegerField(read_only=True)
    from_timestamp_s = serializers.IntegerField(read_only=True)
    to_timestamp_s = serializers.IntegerField(read_only=True)
    clean_air_medal = serializers.BooleanField(read_only=True)
    airq_hist = serializers.DictField(read_only=True)
    
    url = serializers.HyperlinkedIdentityField(
        view_name="room-detail"
    )

    class Meta:
        model = RoomAirQualityViewModel
        fields = ["url"]

    class JSONAPIMeta:
        resource_name = "room-airquality"

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if args[0].airq_hist is None:
            self.fields.pop("airq_hist")