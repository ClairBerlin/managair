import logging
import simplejson as json  # for correct serialization of decimal geolocation
import toml
import requests
from requests import RequestException
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timezone
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
        stadtpuls_sensor_id = stadtpuls_installation.stadtpuls_sensor_id
    except ObjectDoesNotExist:
        # If no, register a new Sensor with Statdpuls and persist this fact locally
        logging.info(
            "Installation with ID %d does not yet exist with Stadtpuls, creating it...",
            installation.id,
        )
        try:
            stadtpuls_sensor_id = register_sensor(installation)
        except RequestException as error:
            logging.error("Could not register the sensor with Stadtpuls: %s", error)
            return
        else:
            sp_sensor = StadpulsSensor(
                installation=installation,
                inserted_s=round(datetime.now().timestamp()),
                stadtpuls_sensor_id=stadtpuls_sensor_id,
            )
            sp_sensor.save()

    # insert the sample into Stadpuls.
    logging.info("Publishing sample from %s to Stadtpuls", sender)
    try:
        post_sample(sample, stadtpuls_sensor_id)
    except RequestException as error:
        logging.error(
            "Could not publish sample for node %s, Stadtpuls sensor %s, at timestamp %s. %s",
            sample.node.id,
            stadtpuls_sensor_id,
            sample.timestamp_s,
            error,
        )


def register_sensor(installation):
    login_response = stadtpuls_login()
    user_id = login_response["user"]["id"]
    access_token = login_response["access_token"]

    node = installation.node
    room = installation.room
    site = room.site

    headers = {
        "apikey": settings.SP_API_KEY,
        "Authorization": f"Bearer {access_token}",
        # See discussion  https://github.com/supabase/supabase/discussions/4054
        "prefer": "return=representation",
    }
    # Sensor name is limited to 50 characters.
    sensor_name = f"{node.id}::{installation.from_timestamp_s}"
    req_body = {
        "name": sensor_name,
        "description": installation_to_toml(installation),
        "connection_type": "http",
        "location": site.address.city,
        "longitude": site.address.longitude,
        "latitude": site.address.latitude,
        "user_id": user_id,
        "category_id": 1,  # CO2 measurements
    }
    logging.debug("Setting up new sensor %s at %s", node.id, settings.SP_SUPABASE_URL)
    response = requests.post(
        settings.SP_SENSOR_ENDPOINT, headers=headers, json=req_body
    )
    response.raise_for_status()
    json_response = json.loads(response.content)
    return json_response[0]["id"]


def stadtpuls_login():
    headers = {"apikey": settings.SP_API_KEY}
    params = {"grant_type": "password"}
    req_body = {"email": settings.SP_LOGIN_EMAIL, "password": settings.SP_LOGIN_PWD}
    logging.debug(
        "Logging into Stadtpuls Supabase %s as user %s",
        settings.SP_LOGIN_ENDPOINT,
        settings.SP_LOGIN_EMAIL,
    )
    response = requests.post(
        url=settings.SP_LOGIN_ENDPOINT, params=params, headers=headers, json=req_body
    )
    response.raise_for_status()
    return response.json()


def installation_to_toml(installation):
    node = installation.node
    model = node.model
    room = installation.room
    site = room.site
    owner = site.operator

    sp_sensor = {"eui64": node.eui64, "alias": node.alias, "owner": owner.name}
    sp_sensor["model"] = {"manufacturer": model.manufacturer, "type": model.trade_name}
    sp_sensor["room"] = {
        "name": room.name,
        "description": room.description,
        "size_sqm": room.size_sqm,
        "height_m": room.height_m,
    }
    sp_sensor["site"] = {
        "name": site.name,
        "description": site.description,
        "street": site.address.street1,
        "zip": site.address.zip,
        "city": site.address.city,
    }
    return toml.dumps(sp_sensor)


def post_sample(sample, stadtpuls_sensor_id):
    headers = {"Authorization": f"Bearer {settings.SP_AUTH_TOKEN}"}
    timestamp = datetime.fromtimestamp(sample.timestamp_s, timezone.utc)
    timestamp_iso = timestamp.isoformat()
    req_body = {
        "records": [
            {"recorded_at": timestamp_iso, "measurements": [sample.co2_ppm]}
        ]
    }
    records_endpoint = f"{settings.SP_RECORDS_ENDPOINT}/{stadtpuls_sensor_id}/records"
    response = requests.post(url=records_endpoint, headers=headers, json=req_body)
    response.raise_for_status()
