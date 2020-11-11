from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed
from rest_framework.filters import SearchFilter
from rest_framework_json_api import filters
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from core.models import (
    Quantity,
    NodeProtocol,
    NodeModel,
    Node,
    NodeFidelity,
    Membership,
)
from core.serializers import (
    QuantitySerializer,
    NodeProtocolSerializer,
    NodeModelSerializer,
    NodeSerializer,
    NodeFidelitySerializer,
)


class QuantityViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer


class NodeProtocolViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeProtocol.objects.all()
    serializer_class = NodeProtocolSerializer


class NodeModelViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeModel.objects.all()
    serializer_class = NodeModelSerializer


class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission that allows only the OWNERS of an organization to add, modify or delete a node owned by this orgnization.
    """

    def has_create_permission(self, request, validated_data):
        """Authorize a new resource to be created.

        This is not a method overwritten on BasePermission, but a custom method necessary for our access policy that depends on the incoming resource.
        
        This method must be called after deserialization and validation of the incoming request data to prevent injection attacks. To my understanding, the only place to do so on a generic viewset is in the `perform_create()` method. Thus: Overwrite `perform_create()` on your viewset and call the present method there.
        """
        if request.method == "POST":
            # Is the authorized user an OWNER of the organization to which the node
            # is to be added?

            organization = validated_data["owner"]
            try:
                membership = request.user.memberships.get(
                    organization__id=organization.id
                )
            except Membership.DoesNotExist:
                raise PermissionDenied
            return membership.isOwner()
        else:
            # Should never happen.
            raise MethodNotAllowed(request.method)
    
    @classmethod
    def has_object_permission(cls, request, view, obj):
        """Permissions at the object-level are important for existing nodes."""

        if request.method in ["PUT", "PATCH", "DELETE"]:
            # Is the authorized user an OWNER of the organization that owns the node
            # that is to be modified?
            try:
                owning_organization = obj.get_owner()
                membership = request.user.memberships.get(
                    organization__id=owning_organization.id
                )
            except Membership.DoesNotExist:
                raise PermissionDenied
            return membership.isOwner()

        else:
            return True


class NodeViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationOwner]
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    filter_backends = (filters.QueryParameterValidationFilter, SearchFilter)
    search_fields = ("alias", "eui64")

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(NodeViewSet, self).get_queryset()
        queryset = queryset.filter(owner__users=self.request.user)
        if self.action == "list":
            organization_id = self.request.query_params.get(
                "filter[organization]", None
            )
            if organization_id is not None:
                queryset = queryset.filter(owner=organization_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """Inject permission checking on the validated incoming resource data."""
        if IsOrganizationOwner().has_create_permission(
            self.request, serializer.validated_data
        ):
            super(NodeViewSet, self).perform_create(serializer)
        else:
            raise PermissionDenied


class NodeFidelityViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeFidelity.objects.all()
    serializer_class = NodeFidelitySerializer
