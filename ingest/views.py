from django.shortcuts import render
from rest_framework import generics

from core.models import Sample
from .serializers import SampleIngestSerializer

class InternalSampleView(generics.ListCreateAPIView):
    """View for data ingestion. Must not be exposed externally"""
    queryset = Sample.objects.all()
    serializer_class = SampleIngestSerializer