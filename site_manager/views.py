from rest_framework import permissions
from rest_framework_json_api.views import viewsets
from django.contrib.auth.mixins import LoginRequiredMixin

from site_manager.models import Address, NodeInstallation, Site
from site_manager.serializers import AddressSerializer, NodeInstallationSerializer, SiteSerializer


class AddressViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(AddressViewSet, self).get_queryset()
        return queryset.filter(sites__responsible=self.request.user)


class SiteViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(SiteViewSet, self).get_queryset()
        return queryset.filter(responsible=self.request.user)

class NodeInstallationViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeInstallation.objects.all()
    serializer_class = NodeInstallationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(NodeInstallationViewSet, self).get_queryset()
        return queryset.filter(site__responsible=self.request.user)    