from django.urls import include, path
from rest_framework import routers
from device_manager import views

router = routers.DefaultRouter()
router.register(r'quantities', views.QuantityViewSet)
router.register(r'protocols', views.NodeProtocolViewSet)
router.register(r'models', views.NodeModelViewSet)
router.register(r'nodes', views.NodeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]