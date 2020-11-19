import logging
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
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

from core.queryfilters import IncludeTimeseriesQPValidator

logger = logging.getLogger(__name__)


User = get_user_model()


class SiteNotFoundExceptionView(generics.RetrieveAPIView):
    """This view returns a 404 Not Found exception."""

    queryset = Site.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SiteSerializer

    def get(self, request, *args, **kwargs):
        raise NotFound()  # (detail="Error 404, page not found", code=404)


class UserViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    # Use different serializers for different actions.
    # See https://stackoverflow.com/questions/22616973/django-rest-framework-use-different-serializers-in-the-same-modelviewset
    serializer_classes = {"list": UsernameSerializer, "retrieve": UserSerializer}
    serializer_class = UserSerializer  # fallback
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("username", "email")

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()

        if "user_pk" in self.kwargs:
            # If this viewset is accessed via the 'organization-related' route,
            # it will have been passed the `user_pk` kwarg, and the queryset
            # needs to be filtered accordingly;
            user_pk = self.kwargs["user_pk"]
            queryset = queryset.filter(pk=user_pk)
        else:
            if self.action == "list":
                # For the list view, return just the username of all users
                queryset = queryset.only("username")
                organization_id = self.request.query_params.get(
                    "filter[organization]", None
                )
                if organization_id:
                    logger.debug(
                        "Restrict query to members of organization #%s.",
                        organization_id,
                    )
                    queryset = queryset.filter(organizations=organization_id)
            else:
                # Otherwise, return those users only that are in an organization
                # accessible by the logged-in user. Need to make the filter result
                # distinct because the underlying JOIN might return the same user
                # multiple times if it is a member of several organizations.
                logger.debug(
                    "Restrict query to members of the logged-in users' organizations."
                )
                queryset = queryset.filter(
                    organizations__users=self.request.user.id
                ).distinct()
        return queryset

    def get_serializer_class(self):
        # TODO: Does not work for related fields because of this upstream bug:
        # https://github.com/django-json-api/django-rest-framework-json-api/issues/859
        return self.serializer_classes.get(self.action, self.serializer_class)


class UserRelationshipView(RelationshipView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects
    self_link_view_name = "user-relationships"


class AddressViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user"""
        queryset = super().get_queryset()
        return queryset.filter(sites__operator__users=self.request.user).distinct()


class SiteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("name", "description")

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user or to sites that contain node installations marked as public."""
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed sites to those that contain public
            # node installations.
            return queryset.filter(rooms__installations__is_public=True)
        else:
            # User is authenticated.
            queryset = queryset.filter(operator__users=self.request.user)
            if self.action == "list":
                organization_id = self.request.query_params.get(
                    "filter[organization]", None
                )
                if organization_id:
                    logger.debug(
                        "Restrict query to sites of organization #%s.", organization_id
                    )
                    queryset = queryset.filter(operator=organization_id)
            return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied


class RoomViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("name", "description")

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user or to rooms that contain node installations marked as public."""
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed rooms to those that contain public
            # node installations.
            return queryset.filter(installations__is_public=True)
        else:
            queryset = queryset.filter(site__operator__users=self.request.user)
            if self.action == "list":
                organization_id = self.request.query_params.get(
                    "filter[organization]", None
                )
                if organization_id:
                    logger.debug(
                        "Restrict query to rooms of organization #%s.", organization_id
                    )
                    queryset = queryset.filter(site__operator=organization_id)
                site_id = self.request.query_params.get("filter[site]", None)
                if site_id:
                    logger.debug("Restrict query to rooms of site #%s.", site_id)
                    queryset = queryset.filter(site=site_id)
            return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied


class RoomNodeInstallationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = RoomNodeInstallation.objects
    serializer_class = RoomNodeInstallationSerializer
    filter_backends = [IncludeTimeseriesQPValidator]

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user or to node installations marked as public."""
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            # Public API access. Restrict to public node installations.
            return queryset.filter(is_public=True)
        else:
            queryset = queryset.filter(room__site__operator__users=self.request.user)
            if self.action == "list":
                organization_id = self.request.query_params.get(
                    "filter[organization]", None
                )
                if organization_id:
                    logger.debug(
                        "Restrict query to installations of organization #%s.",
                        organization_id,
                    )
                    queryset = queryset.filter(room__site__operator=organization_id)
                site_id = self.request.query_params.get("filter[site]", None)
                if site_id:
                    logger.debug(
                        "Restrict query to installations at site #%s.", site_id
                    )
                    queryset = queryset.filter(room__site=site_id)
                room_id = self.request.query_params.get("filter[room]", None)
                if room_id:
                    logger.debug(
                        "Restrict query to installations in room #%s.", room_id
                    )
                    queryset = queryset.filter(room=room_id)
                node_id = self.request.query_params.get("filter[node]", None)
                if node_id:
                    logger.debug("Restrict query to installations of node %s.", node_id)
                    queryset = queryset.filter(node=node_id)
            return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        installations = []
        for installation in queryset:
            installation.sample_count = (
                installation.node.samples.filter(
                    timestamp_s__gte=installation.from_timestamp_s,
                    timestamp_s__lte=installation.to_timestamp_s,
                ).count()
            )
            installation.query_timestamp_s = round(datetime.now().timestamp())
            installations.append(installation)
        page = self.paginate_queryset(installations)
        # TODO: Simplify to use the parent list method and simply inject the modified
        # queryset.
        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        installation = self.get_object()
        # Limit time-slice to node installation and query.
        install_from_s = installation.from_timestamp_s
        install_to_s = installation.to_timestamp_s
        filter_from_s = int(self.request.query_params.get("filter[from]", 0))
        filter_to_s = int(self.request.query_params.get(
            "filter[to]", round(datetime.now().timestamp())
        ))
        from_max_s = max(install_from_s, filter_from_s)
        to_min_s = min(install_to_s, filter_to_s)
        logger.debug(
            "Limiting the time series to the time slice from %s to %s",
            from_max_s,
            to_min_s,
        )
        sample_queryset = installation.node.samples.filter(
            timestamp_s__gte=from_max_s,
            timestamp_s__lte=to_min_s,
        ).distinct()
        installation.sample_count = sample_queryset.count()
        installation.query_timestamp_s = round(datetime.now().timestamp())
        include_queryparam = self.request.query_params.get("include_timeseries", False)
        if include_queryparam:
            installation.timeseries = sample_queryset
            serializer = self.get_serializer(installation, include_timeseries=True)
        else:
            serializer = self.get_serializer(installation)
        return Response(serializer.data)


class OrganizationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user or to organizations that contain node installations marked as public."""
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            # Public API access. Restrict to public node installations.
            return queryset.filter(sites__rooms__installations__is_public=True)
        else:
            return queryset.filter(users=self.request.user)

    def perform_create(self, serializer):
        """The user adding the present organization automatically is its OWNER."""
        org = serializer.save()
        Membership.objects.create(
            role=Membership.OWNER, user=self.request.user, organization=org
        )


class OrganizationRelationshipView(RelationshipView):
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects
    self_link_view_name = "organization-relationships"
    http_method_names = ["get", "post", "delete", "options", "head"]


class MembershipViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated & IsOrganizationOwner]
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self, *args, **kwargs):
        """Restrict to users in the same organization."""
        queryset = super().get_queryset()
        queryset = queryset.filter(organization__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id:
                logger.debug(
                    "Restrict query to memberships of organization #%s.",
                    organization_id,
                )
                queryset = queryset.filter(organization=organization_id)
            username = self.request.query_params.get("filter[username]", None)
            if username:
                logger.debug("Restrict query to memberships of user %s.", username)
                queryset = queryset.filter(user__username=username)
            user_id = self.request.query_params.get("filter[user]", None)
            if user_id:
                logger.debug(
                    "Restrict query to memberships of the user with id %s.", username
                )
                queryset = queryset.filter(user=user_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied