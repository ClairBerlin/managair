from device_manager.models import NodeProtocol, NodeModel, Node
from device_manager.serializers import NodeProtocolSerializer, NodeModelSerializer, NodeSerializer
from rest_framework import viewsets

class NodeProtocolViewSet(viewsets.ModelViewSet):
    queryset = NodeProtocol.objects.all()
    serializer_class = NodeProtocolSerializer

class NodeModelViewSet(viewsets.ModelViewSet):
    queryset = NodeModel.objects.all()
    serializer_class = NodeModelSerializer

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer