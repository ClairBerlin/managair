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
router.register(r"rooms", inventory.RoomViewSet)
router.register(r"address", inventory.AddressViewSet)
router.register(r"organizations", inventory.OrganizationViewSet)
router.register(r"membership", inventory.MembershipViewSet)
router.register(r"users", inventory.UserViewSet, basename="user")

# Data views
router.register(r"samples", data.SampleViewSet)
router.register(r"timeseries", data.TimeseriesViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # re_path(r'^sites/(?P<pk>[^/.]+)/relationships/(?P<related_field>[^/.]+)$',
    path(
        "sites/<pk>/relationships/<related_field>",
        view=inventory.SiteRelationshipView.as_view(),
        name="site-relationships",
    ),
    path(
        "sites/<pk>/<related_field>/",
        inventory.SiteViewSet.as_view({"get": "retrieve_related"}),
        name="site-related",
    ),
]
