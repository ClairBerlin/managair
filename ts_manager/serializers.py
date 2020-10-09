from rest_framework_json_api import serializers
from ts_manager.models import Sample
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

class TimeseriesSerializer(serializers.Serializer):
    alias = serializers.CharField(max_length=30)
    query_timestamp = serializers.IntegerField()
    from_timestamp = serializers.IntegerField()
    to_timestamp = serializers.IntegerField()
    sample_count = serializers.IntegerField()
    
    class Meta:
        model = TimeseriesViewModel


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