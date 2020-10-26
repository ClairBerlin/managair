from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
    RelationshipView,
)

from core.models import Address, Site, Room, Organization, Membership
from core.serializers import (
    AddressSerializer,
    SiteSerializer,
    RoomSerializer,
    OrganizationSerializer,
    MembershipSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permissions = [permissions.IsAuthenticated]

    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super(UserViewSet, self).get_queryset()

        # If this viewset is accessed via the 'organization-members-list' route,
        # it wll have been passed the `user_pk` kwarg, and the queryset
        # needs to be filtered accordingly; if it was accessed via the
        # unnested '/users' route, the queryset should include all Users
        if "user_pk" in self.kwargs:
            user_pk = self.kwargs["user_pk"]
            queryset = queryset.filter(user__pk=user_pk)

        return queryset


class AddressViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(AddressViewSet, self).get_queryset()
        return queryset.filter(
            sites__operated_by__user_membership__user=self.request.user
        )


class SiteViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(SiteViewSet, self).get_queryset()
        return queryset.filter(operated_by__user_membership__user=self.request.user)


class SiteRelationshipView(RelationshipView):
    queryset = Site.objects
    self_link_view_name = "site-relationships"


class RoomViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(RoomViewSet, self).get_queryset()
        return queryset.filter(
            site__operated_by__user_membership__user=self.request.user
        )


class OrganizationViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(OrganizationViewSet, self).get_queryset()
        return queryset.filter(user_membership__user=self.request.user)


class OrganizationRelationshipView(LoginRequiredMixin, RelationshipView):
    queryset = Organization.objects


class MembershipViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(MembershipViewSet, self).get_queryset()
        return queryset.filter(user=self.request.user)
