from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
    RelationshipView,
    generics,
)

from core.models import (
    Address,
    Site,
    Room,
    Organization,
    Membership,
    RoomNodeInstallation,
)
from core.serializers import (
    AddressSerializer,
    SiteSerializer,
    RoomSerializer,
    RoomNodeInstallationSerializer,
    OrganizationSerializer,
    MembershipSerializer,
    UserSerializer,
)

User = get_user_model()


class SiteNotFoundExceptionView(LoginRequiredMixin, generics.RetrieveAPIView):
    """This view returns a 404 Not Found exception."""

    queryset = Site.objects.all()
    permissions = [permissions.IsAuthenticated]
    serializer_class = SiteSerializer

    def get(self, request, *args, **kwargs):
        raise NotFound()  # (detail="Error 404, page not found", code=404)


class UserViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super(UserViewSet, self).get_queryset()

        # If this viewset is accessed via the 'organization-members-list' route,
        # it wll have been passed the `user_pk` kwarg, and the queryset
        # needs to be filtered accordingly; if it was accessed via the
        # unnested '/users' route, the queryset should include the logged-in user only.
        if "user_pk" in self.kwargs:
            user_pk = self.kwargs["user_pk"]
            queryset = queryset.filter(pk=user_pk)
        else:
            queryset = queryset.filter(pk=self.request.user.id)
        return queryset


class UserRelationshipView(RelationshipView):
    queryset = User.objects
    self_link_view_name = "user-relationships"


class AddressViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(AddressViewSet, self).get_queryset()
        return queryset.filter(sites__operated_by__users=self.request.user)


class SiteViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(SiteViewSet, self).get_queryset()
        return queryset.filter(operated_by__users=self.request.user)


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
        return queryset.filter(site__operated_by__users=self.request.user)


class RoomRelationshipView(LoginRequiredMixin, RelationshipView):
    queryset = Room.objects
    self_link_view_name = "room-relationships"


class RoomNodeInstallationViewSet(LoginRequiredMixin, ModelViewSet):
    permissions = [permissions.IsAuthenticated]
    queryset = RoomNodeInstallation.objects
    serializer_class = RoomNodeInstallationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(RoomNodeInstallationViewSet, self).get_queryset()
        return queryset.filter(room__site__operated_by__users=self.request.user)


class OrganizationViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(OrganizationViewSet, self).get_queryset()
        return queryset.filter(users=self.request.user)

    def perform_create(self, serializer):
        org = serializer.save()
        Membership.objects.create(
            role=Membership.OWNER, user=self.request.user, organization=org
        )


class OrganizationRelationshipView(LoginRequiredMixin, RelationshipView):
    queryset = Organization.objects
    self_link_view_name = "organization-relationships"
    http_method_names = ["get", "post", "delete", "options", "head"]


class MembershipViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(MembershipViewSet, self).get_queryset()
        return queryset.filter(user=self.request.user)
