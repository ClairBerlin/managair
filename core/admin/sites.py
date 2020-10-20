from django.contrib import admin

from core.models import Address, Site, NodeInstallation, Node

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display= ['street1', 'street2', 'zip', 'city']


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(NodeInstallation)
class NodeInstallationAdmin(admin.ModelAdmin):
    list_display = ['node', 'site', 'from_iso', 'to_iso']
