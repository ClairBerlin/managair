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
router.register(r"memberships", inventory.MembershipViewSet)
router.register(r"sites", inventory.SiteViewSet)
router.register(r"address", inventory.AddressViewSet)
router.register(r"rooms", inventory.RoomViewSet)
router.register(
    r"installations", inventory.RoomNodeInstallationViewSet, basename="installation"
)
# Data views
router.register(r"samples", data.SampleViewSet, basename="sample")
router.register(
    r"node-timeseries", data.NodeTimeSeriesViewSet, basename="node-timeseries"
)
router.register(
    r"installation-timeseries",
    data.InstallationTimeSeriesViewSet,
    basename="installation-timeseries",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "users/<pk>/relationships/<related_field>/",
        view=inventory.UserRelationshipView.as_view(),
        name="user-relationships",
    ),
    path(
        "memberships/<pk>/<related_field>/",
        inventory.MembershipViewSet.as_view({"get": "retrieve_related"}),
        name="membership-related",
    ),
    path(
        "users/<pk>/<related_field>/",
        inventory.UserViewSet.as_view({"get": "retrieve_related"}),
        name="user-related",
    ),
    path(
        "organizations/<pk>/relationships/nodes/",
        view=inventory.SiteNotFoundExceptionView.as_view(),
        name="organization-relationships",
    ),
    path(
        "organizations/<pk>/relationships/sites/",
        view=inventory.SiteNotFoundExceptionView.as_view(),
        name="organization-relationships",
    ),
    path(
        "organizations/<pk>/relationships/memberships/",
        view=inventory.SiteNotFoundExceptionView.as_view(),
        name="organization-relationships",
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
        "sites/<pk>/<related_field>/",
        inventory.SiteViewSet.as_view({"get": "retrieve_related"}),
        name="site-related",
    ),
    path(
        "rooms/<pk>/<related_field>/",
        inventory.RoomViewSet.as_view({"get": "retrieve_related"}),
        name="room-related",
    ),
    path(
        "installations/<installation_pk>/timeseries/",
        data.InstallationTimeSeriesViewSet.as_view({"get": "retrieve"}),
        name="installation-timeseries",
    ),
    path(
        "installations/<pk>/<related_field>/",
        inventory.RoomNodeInstallationViewSet.as_view({"get": "retrieve_related"}),
        name="installation-related",
    ),
    path(
        "nodes/<pk>/samples/", data.SampleListView.as_view(), name="node-samples-list"
    ),
    path(
        "nodes/<node_pk>/timeseries/",
        data.NodeTimeSeriesViewSet.as_view({"get": "retrieve"}),
        name="node-timeseries",
    ),
    path(
        "nodes/<pk>/<related_field>/",
        view=devices.NodeViewSet.as_view({"get": "retrieve_related"}),
        name="node-related",
    ),
]
