from django.urls import include, path
from rest_framework import routers

from site_manager import views

router = routers.DefaultRouter()
router.register(r'sites', views.SiteViewSet)
router.register(r'address', views.AddressViewSet)
router.register(r'installation', views.NodeInstallationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]