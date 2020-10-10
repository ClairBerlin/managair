from rest_framework import permissions
from rest_framework_json_api.views import viewsets

from device_manager.models import Quantity, NodeProtocol, NodeModel, Node
from device_manager.serializers import QuantitySerializer, NodeProtocolSerializer, NodeModelSerializer, NodeSerializer

class QuantityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer

class NodeProtocolViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeProtocol.objects.all()
    serializer_class = NodeProtocolSerializer

class NodeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = NodeModel.objects.all()
    serializer_class = NodeModelSerializer

class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def get_queryset(self):
        """Restrict to logged-in user"""
        queryset = super(NodeViewSet, self).get_queryset()
        return queryset.filter(node_installations__site__responsible=self.request.user)