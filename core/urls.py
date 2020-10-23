from django.urls import include, path
from rest_framework import routers

from core.views import data, devices, inventory

router = routers.DefaultRouter()
# Device management views
router.register(r"quantities", devices.QuantityViewSet)
router.register(r"protocols", devices.NodeProtocolViewSet)
router.register(r"models", devices.NodeModelViewSet)
router.register(r"nodes", devices.NodeViewSet)
router.register(r"fidelity", devices.NodeFidelityViewSet)
# Inventory management views
router.register(r"sites", inventory.SiteViewSet)
router.register(r"address", inventory.AddressViewSet)
router.register(r"installation", inventory.NodeInstallationViewSet)
router.register(r"organization", inventory.OrganizationViewSet)
router.register(r"membership", inventory.MembershipViewSet)
router.register(r"user", inventory.UserViewSet)

# Data views
router.register(r"samples", data.SampleViewSet)
router.register(r"timeseries", data.TimeseriesViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
