from rest_framework_json_api import serializers

from core.data_viewmodels import (
    NodeTimeseriesListViewModel,
    NodeTimeseriesViewModel,
    InstallationTimeseriesListViewModel,
    InstallationTimeseriesViewModel,
)
from core.models import Sample


class SampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sample
        fields = (
            "node",
            "timestamp_s",
            "co2_ppm",
            "temperature_celsius",
            "rel_humidity_percent",
            "url",
        )


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


class NodeTimeseriesSerializer(NodeTimeseriesListSerializer):
    samples = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)

    class Meta:
        resource_name = "node-timeseries"
        model = NodeTimeseriesViewModel
        fields = ["url"]


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


class InstallationTimeSeriesSerializer(InstallationTimeseriesListSerializer):
    samples = serializers.ListField(child=SimpleSampleSerializer(), read_only=True)

    class Meta:
        resource_name = "installation-timeseries"
        model = InstallationTimeseriesViewModel
        fields = ["url"]
