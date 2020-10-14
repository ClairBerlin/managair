from django.contrib import admin

from core.models import Sample

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('timestamp_s', 'node_ref_id', 'co2_ppm')
    list_filter = ['node_ref_id']
