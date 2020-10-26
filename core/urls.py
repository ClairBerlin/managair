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
router.register(r"users", inventory.UserViewSet)

# Data views
router.register(r"samples", data.SampleViewSet)
router.register(r"timeseries", data.TimeseriesViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "users/<pk>/relationships/<related_field>",
        view=inventory.UserRelationshipView.as_view(),
        name="user-relationships",
    ),
    path(
        "users/<pk>/<related_field>/",
        inventory.UserViewSet.as_view({"get": "retrieve_related"}),
        name="user-related",
    ),
    path(
        "organizations/<pk>/relationships/<related_field>",
        view=inventory.OrganizationRelationshipView.as_view(),
        name="organization-relationships",
    ),
    path(
        "organizations/<pk>/<related_field>/",
        inventory.OrganizationViewSet.as_view({"get": "retrieve_related"}),
        name="organization-related",
    ),
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
