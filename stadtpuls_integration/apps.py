from django.apps import AppConfig


class StadtpulsConfig(AppConfig):
    name = "stadtpuls_integration"
    verbose_name = "CityLAB Stadtpuls Integration"

    def ready(self):
        # Implicitly connect a signal handlers decorated with @receiver.
        from . import publisher
