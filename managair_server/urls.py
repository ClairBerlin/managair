"""managair_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
"""
import os
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Allauth account management
    path('accounts/', include('accounts.urls')),
    # The main Clair API for inventory management and data retrievak
    path("api/v1/", include("core.urls")),
    # Data ingestion API
    path("ingest/v1/", include("ingest.urls")),
    # Django Admin UI
    path("admin/", admin.site.urls),
    # Authentication
    path("api/v1/auth/", include("dj_rest_auth.urls")),
    # OpenAPI
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

DEBUG = int(os.environ.get("DEBUG", default=0))
if DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
