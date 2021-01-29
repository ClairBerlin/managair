import logging
from datetime import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_400_BAD_REQUEST
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
    InstallationImageSerializer,
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

        if "organization_pk" in self.kwargs:
            # Viewset is accessed via the 'organization-related' route.
            organization_pk = self.kwargs["organization_pk"]
            logger.debug("Access Users via the organization #%s.", organization_pk)
            queryset = queryset.filter(organizations=organization_pk)
        if "filter[organization]" in self.request.query_params:
            organization_filter = self.request.query_params["filter[organization]"]
            logger.debug(
                "Filter query to members of organization #%s.", organization_filter
            )
            queryset = queryset.filter(organizations=organization_filter)

        if self.action == "list":
            # For the list view, return just the username of all users.
            # This is not secure because other fields can be loaded on demand.
            # Rely on the serializer to return no PII for GET requests.
            queryset = queryset.only("username")
        else:
            # Restrict to users that are in an organization accessible to the
            # authenticated user.
            queryset = queryset.filter(organizations__users=self.request.user.id)

        # Add the currently authenticated user to the queryset
        queryset = queryset | User.objects.filter(pk=self.request.user.id)
        # Need to make the filter result distinct - because the underlying JOIN might
        # return the same entity multiple times.
        return queryset.distinct()

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
        """Restrict to the authenticated user or to sites that contain node installations marked as public."""
        queryset = super().get_queryset()

        is_public = Q(rooms__installations__is_public=True)
        accessible_if_authenticated = Q(operator__users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed sites to those that contain public
            # node installations.
            queryset = queryset.filter(is_public)
        else:
            # User is authenticated.
            queryset = queryset.filter(is_public | accessible_if_authenticated)

        if "organization_pk" in self.kwargs:
            # Viewset is accessed via the 'organization-related' route.
            organization_pk = self.kwargs["organization_pk"]
            logger.debug("Access sites view via organization #%s.", organization_pk)
            queryset = queryset.filter(operator=organization_pk)
        if "filter[organization]" in self.request.query_params:
            # Organization is restricted via query parameter.
            organization_filter = self.request.query_params["filter[organization]"]
            logger.debug(
                "Filter query to sites of organization #%s.", organization_filter
            )
            queryset = queryset.filter(operator=organization_filter)
        return queryset.distinct()

    def get_object(self):
        if "room_pk" in self.kwargs:
            # ViewSet accessed via a related room.
            room_pk = self.kwargs["room_pk"]
            site = get_object_or_404(self.get_queryset(), rooms=room_pk)
            self.check_object_permissions(self.request, site)
            return site
        else:
            return super().get_object()

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
        """Restrict to the authenticated user or to rooms that contain node installations marked as public."""
        queryset = super().get_queryset()

        is_public = Q(installations__is_public=True)
        accessible_if_authenticated = Q(site__operator__users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict the listed rooms to those that contain public
            # node installations.
            queryset = queryset.filter(is_public)
        else:
            queryset = queryset.filter(is_public | accessible_if_authenticated)

        if "site_pk" in self.kwargs:
            # Viewset is accessed via the 'site-related' route.
            site_pk = self.kwargs["site_pk"]
            logger.debug("Access roomes view via site #%s.", site_pk)
            queryset = queryset.filter(site=site_pk)
        if "filter[site]" in self.request.query_params:
            site_filter = self.request.query_params["filter[site]"]
            logger.debug("Filter query to rooms of site #%s.", site_filter)
            queryset = queryset.filter(site=site_filter)
        if "filter[organization]" in self.request.query_params:
            organization_filter = self.request.query_params["filter[organization]"]
            logger.debug(
                "Filter query to rooms of organization #%s.", organization_filter
            )
            queryset = queryset.filter(site__operator=organization_filter)
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
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = RoomNodeInstallation.objects
    serializer_class = RoomNodeInstallationSerializer
    filter_backends = [IncludeTimeseriesQPValidator]

    def get_queryset(self, *args, **kwargs):
        """Restrict to the authenticated user or to node installations marked as public."""
        queryset = super().get_queryset()

        is_public = Q(is_public=True)
        accessible_if_authenticated = Q(node__owner__users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict to public node installations.
            queryset = queryset.filter(is_public)
        else:
            # User is authenticated.
            queryset = queryset.filter(is_public | accessible_if_authenticated)

        if "room_pk" in self.kwargs:
            # Viewset is accessed via the 'room-related' route.
            room_pk = self.kwargs["room_pk"]
            logger.debug("Access installations view via room #%s.", room_pk)
            queryset = queryset.filter(room=room_pk)
        if "filter[room]" in self.request.query_params:
            room_filter = self.request.query_params["filter[room]"]
            logger.debug("Filter query to installations in room #%s.", room_filter)
            queryset = queryset.filter(room=room_filter)
        if "filter[site]" in self.request.query_params:
            site_filter = self.request.query_params["filter[site]"]
            logger.debug("Filter query to installations in site #%s.", site_filter)
            queryset = queryset.filter(room__site=site_filter)
        if "filter[organization]" in self.request.query_params:
            organization_filter = self.request.query_params["filter[organization]"]
            logger.debug(
                "Filter query to installations in organization #%s.",
                organization_filter,
            )
            queryset = queryset.filter(room__site__operator=organization_filter)
        if "filter[node]" in self.request.query_params:
            node_filter = self.request.query_params["filter[node]"]
            logger.debug("Filter query to installations of node #%s.", node_filter)
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
            installation.sample_count = installation.node.samples.filter(
                timestamp_s__gte=installation.from_timestamp_s,
                timestamp_s__lte=installation.to_timestamp_s,
            ).count()
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
        filter_to_s = int(
            self.request.query_params.get(
                "filter[to]", round(datetime.now().timestamp())
            )
        )
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

    @action(
        detail=True,
        methods=["PUT"],
        serializer_class=InstallationImageSerializer,
        parser_classes=[MultiPartParser],
        # url_name="installation-image"
    )
    def image(self, request, pk):
        """Action to upload an installation image via a PUT request.
        See https://www.trell.se/blog/file-uploads-json-apis-django-rest-framework/
        """
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, HTTP_400_BAD_REQUEST)


class OrganizationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly & IsOrganizationOwner]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self, *args, **kwargs):
        """Restrict to logged-in user or to organizations that contain node installations marked as public."""
        queryset = super().get_queryset()

        is_public = Q(nodes__installations__is_public=True)
        accessible_if_authenticated = Q(users=self.request.user)

        if not self.request.user.is_authenticated:
            # Public API access. Restrict to public node installations.
            queryset = queryset.filter(is_public)
        else:
            queryset = queryset.filter(is_public | accessible_if_authenticated)

        return queryset.distinct()

    def get_object(self):
        if "site_pk" in self.kwargs:
            # ViewSet accessed via a related site.
            site_pk = self.kwargs["site_pk"]
            organization = get_object_or_404(self.get_queryset(), sites=site_pk)
            self.check_object_permissions(self.request, organization)
            return organization
        else:
            return super().get_object()

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
        # Restrict to memberships of users that are in an organization accessible to the
        # authenticated user.
        queryset = queryset.filter(organization__users=self.request.user)

        if "organization_pk" in self.kwargs:
            # Viewset is accessed via the 'organization-related' route.
            organization_pk = self.kwargs["organization_pk"]
            logger.debug("Access Users via the organization #%s.", organization_pk)
            queryset = queryset.filter(organization=organization_pk)
        if "filter[organization]" in self.request.query_params:
            organization_filter = self.request.query_params["filter[organization]"]
            logger.debug("Filter membership to organization #%s.", organization_filter)
            queryset = queryset.filter(organization=organization_filter)
        if "filter[username]" in self.request.query_params:
            username_filter = self.request.query_params["filter[username]"]
            logger.debug("Filter membership to username #%s.", username_filter)
            queryset = queryset.filter(user__username=username_filter)
        if "filter[user]" in self.request.query_params:
            user_filter = self.request.query_params["filter[user]"]
            logger.debug("Filter membership to user #%s.", user_filter)
            queryset = queryset.filter(user=user_filter)
        # Need to make the filter result distinct because the underlying JOIN might
        # return the same entity multiple times.
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        # TODO: Refactor into common base class.
        # TODO: Allow ASSISTANTS to change rooms.
        if IsOrganizationOwner.has_create_permission(self.request, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied
