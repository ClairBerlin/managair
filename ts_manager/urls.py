from django.urls import include, path
from rest_framework import routers

from ts_manager import views


router = routers.DefaultRouter()
router.register(r'samples', views.SampleViewSet)
router.register(r'timeseries', views.TimeseriesViewSet)

urlpatterns = [
    path('ingest/', views.InternalSampleView.as_view(), name='ingest'),
    path('', include(router.urls)),
]
