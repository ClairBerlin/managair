"""managair_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url

urlpatterns = [
    url(r"^", include("user_manager.urls")),
    path('api/auth/', include('rest_framework.urls')),
    url('api/devices/v1/', include("device_manager.urls")),
    url('api/sites/v1/', include("site_manager.urls")),
    url('api/data/v1/', include("ts_manager.urls")),
    path('admin/', admin.site.urls),
]
