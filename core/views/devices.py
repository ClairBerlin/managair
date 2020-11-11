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
    Permission that allows only the OWNERS of an organization to add, modify or delete a node.
    """

    def has_permission(self, request, view):
        """Permissions at the request-level are relevant for new nodes."""
        if request.method == "POST":
            # Is the authorized user an OWNER of the organization to which the node
            # is to be added?
            organization_id = request.data["owner"]["id"]
            try:
                membership = request.user.memberships.get(
                    organization__id=organization_id
                )
            except Membership.DoesNotExist:
                raise PermissionDenied
            return membership.isOwner()
        elif request.method in permissions.SAFE_METHODS or request.method in [
            "PUT",
            "PATCH",
            "DELETE",
        ]:
            # Safe methods are handled by filtering the queryset in get_queryset.
            # PUT and PATCH are handled at the object level.
            return True
        else:
            # Should not exist
            raise MethodNotAllowed(request.method)

    def has_object_permission(self, request, view, obj):
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


class NodeFidelityViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeFidelity.objects.all()
    serializer_class = NodeFidelitySerializer
