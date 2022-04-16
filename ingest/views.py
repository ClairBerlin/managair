import logging
from rest_framework import generics
from django.conf import settings

from core.models import Sample
from .serializers import SampleIngestSerializer
from .signals import publish_sample


logger = logging.getLogger(__name__)


class InternalSampleView(generics.ListCreateAPIView):
    """View for data ingestion. Must not be exposed externally"""

    queryset = Sample.objects.all()
    serializer_class = SampleIngestSerializer

    def perform_create(self, serializer):
        """Hook to trigger forwarding to external IOT data platforms."""
        sample = serializer.save()
        if (settings.IOTDP_INTEGRATION):
            self.__publish_sample(sample)

    def __publish_sample(self, sample):
        """Publish a signal for an incoming sample whose installation is public."""
        
        logger.debug(
            "Examining publication of incoming sample from node %s", sample.node.id
        )
        installations = sample.node.installations
        current_installation = installations.filter(
            from_timestamp_s__lte=sample.timestamp_s,
            to_timestamp_s__gte=sample.timestamp_s,
        )
        if current_installation.count() == 1 and current_installation[0].is_public:
            logger.info(
                "Publishing sample at timestamp %d fron node %s",
                sample.timestamp_s,
                sample.node.id,
            )
            publish_sample.send(
                sender=self.__class__, sample=sample, installation=current_installation[0]
            )
