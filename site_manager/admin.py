from django.contrib import admin
from site_manager.models import Address, Site, NodeInstallation
from device_manager.models import Node

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display= ['street1', 'street2', 'zip', 'city']


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(NodeInstallation)
class NodeInstallationAdmin(admin.ModelAdmin):
    list_display = ['node', 'site', 'from_timestamp', 'to_timestamp']
