import logging
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from ingest.signals import publish_sample
from ingest.views import InternalSampleView
from .models import StadpulsSensor

logger = logging.getLogger(__name__)

@receiver(publish_sample, sender=InternalSampleView)
def publish_to_stadtpuls(sender, **kwargs):
    sample = kwargs["sample"]
    installation = kwargs["installation"]
    # Query the DB if the given installation was already set up in Stadtpuls.
    try:
        stadtpuls_installation = StadpulsSensor.objects.get(
            installation=installation.id
        )
    except ObjectDoesNotExist:
        # If no, register a new Sensor with Statdpuls and persist this fact locally
        logging.info(
            "Installation with ID %d does not yet exist with Stadtpuls, creating it...",
            installation.id,
        )

    # insert the sample into Stadpuls.
    logging.info("Publishing sample from %s to Stadtpuls", sender)
