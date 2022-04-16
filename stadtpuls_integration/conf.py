from appconf import AppConf
from django.conf import settings


class StadtpulsAppConf(AppConf):
    SUPABASE_URL = "https://porgaqmrgwwrbwahohml.supabase.co"
    LOGIN_ENDPOINT = "https://porgaqmrgwwrbwahohml.supabase.co/auth/v1/token"
    SENSOR_ENDPOINT = "https://porgaqmrgwwrbwahohml.supabase.co/rest/v1/sensors"
    RECORDS_ENDPOINT = "https://stadtpuls-api-v3-staging.onrender.com/api/v3/sensors"
    API_KEY = ""
    LOGIN_EMAIL = ""
    LOGIN_PWD = ""
    AUTH_TOKEN = ""

    class Meta:
        prefix = "sp"
