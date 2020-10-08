from django.contrib import admin
from device_manager.models import Quantity, NodeModel, NodeProtocol, Node

@admin.register(Quantity)
class QuantityAdmin(admin.ModelAdmin):
    pass

@admin.register(NodeProtocol)
class NodeProtocolAdmin(admin.ModelAdmin):
    pass

class NodesInline(admin.TabularInline):
    model = Node

@admin.register(NodeModel)
class NodeModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'sensor_type')
    inlines = [NodesInline]

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('alias', 'id', 'device_id', 'model')
    list_filter = ['model']