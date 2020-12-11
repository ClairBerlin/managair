from django.contrib import admin

from core.models import (
    Address,
    Site,
    Room,
    RoomNodeInstallation,
    Organization,
    Membership,
)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["street1", "street2", "zip", "city"]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "operator", "address"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "site"]


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


@admin.register(RoomNodeInstallation)
class RoomNodeInstallationAdmin(admin.ModelAdmin):
    list_display = ["node", "room", "is_public", "from_iso", "to_iso", "image"]