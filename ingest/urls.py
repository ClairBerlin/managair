from django.urls import path

from .views import InternalSampleView

urlpatterns = [
    path("ingest/", InternalSampleView.as_view(), name="ingest"),
]
