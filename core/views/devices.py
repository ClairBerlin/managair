from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework import permissions
from rest_framework_json_api.views import viewsets

from core.models import Quantity, NodeProtocol, NodeModel, Node, NodeFidelity
from core.serializers import QuantitySerializer, NodeProtocolSerializer, NodeModelSerializer, NodeSerializer, NodeFidelitySerializer

class QuantityViewSet(LoginRequiredMixin,viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer

class NodeProtocolViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeProtocol.objects.all()
    serializer_class = NodeProtocolSerializer

class NodeModelViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeModel.objects.all()
    serializer_class = NodeModelSerializer

class NodeViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(NodeViewSet, self).get_queryset()
        return queryset.filter(node_installations__site__responsible=self.request.user)

class NodeFidelityViewSet(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = NodeFidelity.objects.all()
    serializer_class = NodeFidelitySerializer
