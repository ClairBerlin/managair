from django.contrib import admin
from device_manager.models import Quantity, NodeModel, NodeProtocol, Node

class QuantityAdmin(admin.ModelAdmin):
    pass

class NodeProtocolAdmin(admin.ModelAdmin):
    pass

class NodeModelAdmin(admin.ModelAdmin):
    pass

class NodeAdmin(admin.ModelAdmin):
    pass

admin.site.register(Quantity, QuantityAdmin)
admin.site.register(NodeProtocol, NodeProtocolAdmin)
admin.site.register(NodeModel, NodeModelAdmin)
admin.site.register(Node, NodeAdmin)
