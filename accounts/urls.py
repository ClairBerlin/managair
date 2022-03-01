from django.urls import include, path
from .views import account_signup_view

urlpatterns = [
    path("signup/", view=account_signup_view),
    path("", include("allauth.urls")),
]
