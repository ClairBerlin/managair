from rest_framework_json_api import serializers
from ts_manager.models import Sample
from device_manager.models import Node
from ts_manager.viewmodels import TimeseriesViewModel


class SampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sample
        fields = (
            'node_ref',
            'timestamp_s',
            'co2_ppm',
            'temperature_celsius',
            'rel_humidity_percent',
            'url'
            )

class SampleIngestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = (
            'node_ref',
            'timestamp_s',
            'co2_ppm',
            'temperature_celsius',
            'rel_humidity_percent',
            )

class TimeseriesSerializer(serializers.Serializer):
    alias = serializers.CharField(max_length=30)
    query_timestamp = serializers.IntegerField()
    from_timestamp = serializers.IntegerField()
    to_timestamp = serializers.IntegerField()
    sample_count = serializers.IntegerField()
    
    class Meta:
        model = TimeseriesViewModel
        fields = ['url']


class SimpleSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        exclude = ['node_ref', 'id']


class SampleListSerializer(serializers.Serializer):
    query_timestamp = serializers.IntegerField()
    from_timestamp = serializers.IntegerField()
    to_timestamp = serializers.IntegerField()
    sample_count = serializers.IntegerField()
    samples = serializers.ListField(
        child=SimpleSampleSerializer(),
        read_only=True)
    
    class Meta:
        fields = ['url']

class NodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Node
        fields = ('id', 'device_id', 'alias', 'protocol', 'model', 'url')