from rest_framework_json_api import serializers

from core.models import Sample, NodeInstallation

class SampleIngestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = (
            'node_ref_id',
            'timestamp_s',
            'co2_ppm',
            'temperature_celsius',
            'rel_humidity_percent',
            )
