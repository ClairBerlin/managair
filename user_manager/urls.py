from django.urls import include, path
from user_manager.views import dashboard, register

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("dashboard/", dashboard, name="dashboard"),
    path("register/", register, name="register"),
]
