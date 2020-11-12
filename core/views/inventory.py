from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied, MethodNotAllowed
from rest_framework.filters import SearchFilter
from rest_framework_json_api import filters
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
    RelationshipView,
    generics,
)

from core.permissions import IsOrganizationOwner
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
    UsernameSerializer,
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
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    # Use different serializers for different actions.
    # See https://stackoverflow.com/questions/22616973/django-rest-framework-use-different-serializers-in-the-same-modelviewset
    serializer_classes = {"list": UsernameSerializer, "retrieve": UserSerializer}
    serializer_class = UserSerializer  # fallback
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("username", "email")

    def get_queryset(self):
        queryset = super(UserViewSet, self).get_queryset()

        # If this viewset is accessed via the 'organization-related' route,
        # it will have been passed the `user_pk` kwarg, and the queryset
        # needs to be filtered accordingly;
        if "user_pk" in self.kwargs:
            user_pk = self.kwargs["user_pk"]
            queryset = queryset.filter(pk=user_pk)
        else:
            if self.action == "list":
                # For the list view, return just the username of all users
                queryset = queryset.only("username")
                organization_id = self.request.query_params.get(
                    "filter[organization]", None
                )
                if organization_id is not None:
                    queryset = queryset.filter(organizations=organization_id)
            else:
                # Otherwise, return those users only that are in an organization
                # accessible by the logged-in user. Need to make the filter result
                # distinct because the underlying JOIN might return the same user
                # multiple times if it is a member of several organizations.
                queryset = queryset.filter(
                    organizations__users=self.request.user.id
                ).distinct()
        return queryset

    def get_serializer_class(self):
        # TODO: Does not work for related fields because of this upstream bug:
        # https://github.com/django-json-api/django-rest-framework-json-api/issues/859
        return self.serializer_classes.get(self.action, self.serializer_class)


class UserRelationshipView(RelationshipView):
    queryset = User.objects
    self_link_view_name = "user-relationships"


class AddressViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(AddressViewSet, self).get_queryset()
        return queryset.filter(sites__operator__users=self.request.user).distinct()


class SiteViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("name", "description")

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(SiteViewSet, self).get_queryset()
        queryset = queryset.filter(operator__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                queryset = queryset.filter(operator=organization_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super(SiteViewSet, self).perform_create(serializer)
        else:
            raise PermissionDenied


class RoomViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("name", "description")

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(RoomViewSet, self).get_queryset()
        queryset = queryset.filter(site__operator__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                queryset = queryset.filter(site__operator=organization_id)
            site_id = self.request.query_params.get("filter[site]", None)
            if site_id is not None:
                queryset = queryset.filter(site=site_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super(RoomViewSet, self).perform_create(serializer)
        else:
            raise PermissionDenied


class RoomNodeInstallationViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    queryset = RoomNodeInstallation.objects
    serializer_class = RoomNodeInstallationSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(RoomNodeInstallationViewSet, self).get_queryset()
        queryset = queryset.filter(room__site__operator__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                queryset = queryset.filter(room__site__operator=organization_id)
            site_id = self.request.query_params.get("filter[site]", None)
            if site_id is not None:
                queryset = queryset.filter(room__site=site_id)
            room_id = self.request.query_params.get("filter[room]", None)
            if room_id is not None:
                queryset = queryset.filter(room=room_id)
            node_id = self.request.query_params.get("filter[node]", None)
            if node_id is not None:
                queryset = queryset.filter(node=node_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super(RoomNodeInstallationViewSet, self).perform_create(serializer)
        else:
            raise PermissionDenied


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
        """Restrict to users in the same organization."""
        queryset = super(MembershipViewSet, self).get_queryset()
        queryset = queryset.filter(organization__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                queryset = queryset.filter(organization=organization_id)
            username = self.request.query_params.get("filter[username]", None)
            if username is not None:
                queryset = queryset.filter(user__username=username)
            user_id = self.request.query_params.get("filter[user]", None)
            if user_id is not None:
                queryset = queryset.filter(user=user_id)
        return queryset.distinct()