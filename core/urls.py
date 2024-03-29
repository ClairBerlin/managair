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
router.register(r"addresses", inventory.AddressViewSet)
router.register(r"rooms", inventory.RoomViewSet)
router.register(
    r"installations", inventory.RoomNodeInstallationViewSet, basename="installation"
)
# Data views
router.register(
    r"node-timeseries", data.NodeTimeSeriesViewSet, basename="node-timeseries"
)
router.register(
    r"installation-timeseries",
    data.InstallationTimeSeriesViewSet,
    basename="installation-timeseries",
)

# Ordering of the following URL patterns from top to bottom matters, because Django 
# takes the first match.
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
        "memberships/<pk>/<related_field>/",
        inventory.MembershipViewSet.as_view({"get": "retrieve_related"}),
        name="membership-related",
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
        "organizations/<organization_pk>/users/",
        inventory.UserViewSet.as_view({"get": "list"}),
        name="organization-related-users",
    ),
    path(
        "organizations/<organization_pk>/memberships/",
        inventory.MembershipViewSet.as_view({"get": "list"}),
        name="organization-related-memberships",
    ),
    path(
        "organizations/<organization_pk>/sites/",
        inventory.SiteViewSet.as_view({"get": "list"}),
        name="organization-related-sites",
    ),
    path(
        "organizations/<organization_pk>/nodes/",
        devices.NodeViewSet.as_view({"get": "list"}),
        name="organization-related-nodes",
    ),
    path(
        "sites/<site_pk>/organization/",
        inventory.OrganizationViewSet.as_view({"get": "retrieve"}),
        name="site-related-organization",
    ),
    path(
        "sites/<site_pk>/rooms/",
        inventory.RoomViewSet.as_view({"get": "list"}),
        name="site-related-rooms",
    ),
    path( # Needed for the address relation only.
        "sites/<pk>/<related_field>/",
        inventory.SiteViewSet.as_view({"get": "retrieve_related"}),
        name="site-related",
    ),   
    path(
        "rooms/<room_pk>/site/",
        inventory.SiteViewSet.as_view({"get": "retrieve"}),
        name="room-related-site",
    ),
    path(
        "rooms/<room_pk>/installations/",
        inventory.RoomNodeInstallationViewSet.as_view({"get": "list"}),
        name="room-related-installations",
    ),
    path(
        "rooms/<pk>/airquality/",
        data.RoomAirQualityViewSet.as_view({"get": "retrieve"}),
        name="room-airquality",
    ),
    path(
        "rooms/<pk>/airquality/<year_month>",
        data.RoomAirQualityViewSet.as_view({"get": "retrieve"}),
        name="room-airquality",
    ),
    path(
        "installations/<installation_pk>/timeseries/",
        data.InstallationTimeSeriesViewSet.as_view({"get": "retrieve"}),
        name="installation-timeseries",
    ),
    path(
        "installations/<installation_pk>/node/",
        devices.NodeViewSet.as_view({"get": "retrieve"}),
        name="installation-related-node",
    ),
    path(
        "installations/<pk>/<related_field>/",
        inventory.RoomNodeInstallationViewSet.as_view({"get": "retrieve_related"}),
        name="installation-related",
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
