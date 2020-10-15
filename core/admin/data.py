from django.contrib import admin

from core.models import Sample

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('timestamp_iso', 'node', 'co2_ppm')
    list_filter = ['node']
