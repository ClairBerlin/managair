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
router.register(r"users", inventory.UserViewSet)
router.register(r"organizations", inventory.OrganizationViewSet)
router.register(r"sites", inventory.SiteViewSet)
router.register(r"address", inventory.AddressViewSet)
router.register(r"rooms", inventory.RoomViewSet)
router.register(r"installations", inventory.RoomNodeInstallationViewSet)
# Data views
router.register(r"samples", data.SampleViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "users/<pk>/relationships/<related_field>/",
        view=inventory.UserRelationshipView.as_view(),
        name="user-relationships",
    ),
    path(
        "users/<pk>/<related_field>/",
        inventory.UserViewSet.as_view({"get": "retrieve_related"}),
        name="user-related",
    ),
    path(
        "organizations/<pk>/relationships/<related_field>/",
        view=inventory.OrganizationRelationshipView.as_view(),
        name="organization-relationships",
    ),
    path(
        "organizations/<pk>/<related_field>/",
        inventory.OrganizationViewSet.as_view({"get": "retrieve_related"}),
        name="organization-related",
    ),
    path(
        "sites/<pk>/relationships/<related_field>/",
        view=inventory.SiteRelationshipView.as_view(),
        name="site-relationships",
    ),
    path(
        "sites/<pk>/<related_field>/",
        inventory.SiteViewSet.as_view({"get": "retrieve_related"}),
        name="site-related",
    ),
    path(
        "rooms/<pk>/relationships/<related_field>/",
        view=inventory.RoomRelationshipView.as_view(),
        name="room-relationships",
    ),
    path(
        "rooms/<pk>/<related_field>/",
        inventory.RoomViewSet.as_view({"get": "retrieve_related"}),
        name="room-related",
    ),
    path(
        "nodes/<pk>/samples/", data.SampleListView.as_view(), name="node-samples-list"
    ),
    path(
        "nodes/<pk>/timeseries/", data.TimeseriesDetailView.as_view(), name="node-timeseries-detail"
    ),
    path(
        "nodes/<pk>/relationships/<related_field>/",
        view=devices.NodeRelationshipView.as_view(),
        name="node-relationships",
    ),
    path(
        "nodes/<pk>/<related_field>/",
        view=devices.NodeViewSet.as_view({"get": "retrieve_related"}),
        name="node-related",
    ),
    path(
        "timeseries/",
        view=data.TimeSeriesListView.as_view(),
        name="timeseries-list"
    ),
    path(
        "timeseries/<pk>/",
        view=data.TimeseriesDetailView.as_view(),
        name="timeseries-detail"
    )
]
