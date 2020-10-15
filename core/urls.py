from django.urls import include, path

from rest_framework import routers

from core.views import devices, sites, data

router = routers.DefaultRouter()
# Device management views
router.register(r'quantities', devices.QuantityViewSet)
router.register(r'protocols', devices.NodeProtocolViewSet)
router.register(r'models', devices.NodeModelViewSet)
router.register(r'nodes', devices.NodeViewSet)
router.register(r'fidelity', devices.NodeFidelityViewSet)
# Site management views
router.register(r'sites', sites.SiteViewSet)
router.register(r'address', sites.AddressViewSet)
router.register(r'installation', sites.NodeInstallationViewSet)
# Data views
router.register(r'samples', data.SampleViewSet)
router.register(r'timeseries', data.TimeseriesViewSet)

urlpatterns = [
    path('', include(router.urls)),
]