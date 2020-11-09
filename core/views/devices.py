from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import permissions
from rest_framework.filters import SearchFilter
from rest_framework_json_api import filters
from rest_framework_json_api.views import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from core.models import Quantity, NodeProtocol, NodeModel, Node, NodeFidelity
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


class NodeViewSet(LoginRequiredMixin, ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
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
                    "filter[organization]", None)
            if organization_id is not None:
                queryset = queryset.filter(owner=organization_id)
        return queryset.distinct()


class NodeFidelityViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeFidelity.objects.all()
    serializer_class = NodeFidelitySerializer
