from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

from rest_framework import permissions
from rest_framework_json_api.views import viewsets

from core.models import Address, NodeInstallation, Site, Organization, \
    Membership
from core.serializers import AddressSerializer, NodeInstallationSerializer, \
    SiteSerializer, OrganizationSerializer, MembershipSerializer, UserSerializer

User = get_user_model()

class UserViewSet(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    

class AddressViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(AddressViewSet, self).get_queryset()
        return queryset.filter(sites__operated_by__user_membership__user=self.request.user)


class SiteViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(SiteViewSet, self).get_queryset()
        return queryset.filter(operated_by__user_membership__user=self.request.user)

class NodeInstallationViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeInstallation.objects.all()
    serializer_class = NodeInstallationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(NodeInstallationViewSet, self).get_queryset()
        return queryset.filter(site__operated_by__user_membership__user=self.request.user)


class OrganizationViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(OrganizationViewSet, self).get_queryset()
        return queryset.filter(user_membership__user=self.request.user)


class MembershipViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(MembershipViewSet, self).get_queryset()
        return queryset.filter(user=self.request.user)
