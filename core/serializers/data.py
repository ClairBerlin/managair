from rest_framework_json_api import serializers

from core.data_viewmodels import TimeseriesViewModel
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
