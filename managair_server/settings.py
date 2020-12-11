"""
Django settings for managair_server project.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from sys import maxsize
from pathlib import Path

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def get_secret_from_env_or_file(secret_name: str):
    """Try to read a secret from a one-line text file, if the file name is provided
    as environment variable <secret_name>_FILE. Otherwise, read the secret from an
    environment vairable <secret_name>."""
    key_file_name = os.environ.get(secret_name + "_FILE", None)
    if key_file_name:
        with open(key_file_name) as f:
            return f.read().strip()
    else:
        return os.environ.get(secret_name)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# The SECRET_KEY can be read from a file (for use with Docker secrets) or from the
# environment.
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret_from_env_or_file("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get("DEBUG", default=0))

# The Debug toolbar is helpful for analyzing DB queries, but very resource-intensive.
DEBUG_TOOLBAR = int(os.environ.get("DEBUG_TOOLBAR", default=0))

# Do not use Sentry reporting with local development stacks.
SENTRY = int(os.environ.get("SENTRY", default=0))

# Enable or disable periodic node fidelity check.
NODE_FIDELITY = int(os.environ.get("NODE_FIDELITY", default=0))

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space
# between each. For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")

# Activate Sentry remote error recording.
if SENTRY:
    sentry_sdk.init(
        dsn=get_secret_from_env_or_file("SENTRY_URL"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.0,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=False,
    )

# Application definition
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django_q",
    "rest_framework",
    "rest_framework.authtoken",
    "bootstrap4",
    "accounts",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "corsheaders",
    "drf_spectacular",
    "core",
    "ingest",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Add the debug toolbar.
# Setup that works with docker. See https://gist.github.com/douglasmiranda/9de51aaba14543851ca3#gistcomment-3277795
if DEBUG_TOOLBAR:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: not request.is_ajax()
    }

ROOT_URLCONF = "managair_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["managair_server/templates/"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

REST_FRAMEWORK = {
    # OpenAPI schema (for DRF-Spectaclar)
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Enable pagination but do not enforce a page size limit.
    "PAGE_SIZE": maxsize,
    "EXCEPTION_HANDLER": "rest_framework_json_api.exceptions.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework_json_api.pagination.JsonApiPageNumberPagination",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework_json_api.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
        # If you're performance testing, you will want to use the browseable API
        # without forms, as the forms can generate their own queries.
        # If performance testing, enable:
        # 'example.utils.BrowsableAPIRendererWithoutForms',
        # Otherwise, to play around with the browseable API, enable:
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_METADATA_CLASS": "rest_framework_json_api.metadata.JSONAPIMetadata",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework_json_api.filters.QueryParameterValidationFilter",
        # 'rest_framework_json_api.filters.OrderingFilter',
        # 'rest_framework_json_api.django_filters.DjangoFilterBackend',
        # 'rest_framework.filters.SearchFilter',
    ),
    "SEARCH_PARAM": "filter[search]",
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "vnd.api+json",
}

# Email Setup
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", default=587))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
# The EMAIL_HOST_PASSWORD can be read from a file (for use with Docker secrets) or from
# the environment.
EMAIL_HOST_PASSWORD = get_secret_from_env_or_file("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = bool(os.environ.get("EMAIL_USE_TLS", default=True))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

# Registration and Authentication
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# See https://dj-rest-auth.readthedocs.io/en/latest/installation.html
REST_SESSION_LOGIN = True
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True  # User needs to provide an email address.
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Clair Plattform] "


WSGI_APPLICATION = "managair_server.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": get_secret_from_env_or_file("SQL_PASSWORD"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

if NODE_FIDELITY:
    # Redis used as broker for the Django_Q task scheduler.
    Q_CLUSTER = {
        "name": "node_check",
        "recycle": 50,
        "timeout": 300,  # 5 minutes to check all nodes.
        "save_limit": 250,
        "cpu_affinity": 1,
        "label": "Live-Node Check",
        "redis": {
            "host": "redis",
            "port": 6379,
            "db": 0,
            "password": None,
            "socket_timeout": None,
            "charset": "utf-8",
            "errors": "strict",
            "unix_socket_path": None,
        },
    }

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
# Comment-out during development only, to use simple passwords in testing.
if not DEBUG:
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Let White Noise compress static files and make them cacheable.
# See http://whitenoise.evans.io/en/stable/index.html
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# Default static files directory
# See https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = "/static/"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING", "formatter": "simple"},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_DB_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": os.environ.get("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}
