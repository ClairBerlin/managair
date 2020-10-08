from django.db import models

# Create your models here.

class Quantity(models.Model):
    quantity = models.CharField(max_length=30, blank=False, unique=True)
    base_unit = models.CharField(max_length=30, blank=False)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.quantity}'

class NodeProtocol(models.Model):
    identifier = models.CharField(max_length=30, blank=False, unique=True)
    num_uplink_msgs = models.PositiveIntegerField(default=1)
    num_downlink_msgs = models.PositiveIntegerField(default=1)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.identifier}'


class NodeModel(models.Model):
    name = models.CharField(max_length=30, blank=False, unique=True)
    trade_name = models.CharField(max_length=30)
    manufacturer = models.CharField(max_length=30, blank=False)
    sensor_type = models.CharField(max_length=100, blank=False)
    quantities = models.ManyToManyField(Quantity, related_name='node_models')

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.name}'


class Node(models.Model):
    id = models.UUIDField(primary_key=True)
    device_id = models.CharField(max_length=32, blank=False, unique=True)
    alias = models.CharField(max_length=30)
    protocol = models.ForeignKey(NodeProtocol, on_delete=models.CASCADE)
    model = models.ForeignKey(NodeModel, on_delete=models.CASCADE)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.alias}: {self.id}'
