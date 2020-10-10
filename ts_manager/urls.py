from django.urls import include, path
from rest_framework import routers

from ts_manager import views


router = routers.DefaultRouter()
router.register(r'samples', views.SampleViewSet)
router.register(r'timeseries', views.TimeseriesViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
