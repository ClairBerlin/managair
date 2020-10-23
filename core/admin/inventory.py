from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from core.models import Address, Site, NodeInstallation, Node, Organization, Membership


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["street1", "street2", "zip", "city"]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "operated_by", "address"]


@admin.register(NodeInstallation)
class NodeInstallationAdmin(admin.ModelAdmin):
    list_display = ["node", "site", "from_iso", "to_iso"]


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = (MembershipInline,)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role"]
