from django.contrib import admin
from ts_manager.models import Sample

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('timestamp_s', 'node_ref', 'co2_ppm')
    list_filter = ['node_ref']
