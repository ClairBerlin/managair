from django.contrib import admin


from .models import StadpulsSensor


@admin.register(StadpulsSensor)
class StadtpulsIntegrationAdmin(admin.ModelAdmin):
    list_display = ("installation", "inserted_iso")

