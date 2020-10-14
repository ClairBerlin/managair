
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

from .devices import Node

class Address(models.Model):
    street1 = models.CharField(max_length=50, null=False, blank=False)
    street2 = models.CharField(max_length=50, null=True, blank=True)
    zip = models.CharField(max_length=5, null=False, blank=False)
    city = models.CharField(max_length=50, null=False, blank=False)
    # TODO: Add geolocation.

    class Meta:
        constraints = [
            # Addresses must be unique, but local differentiation is admissible.
            models.UniqueConstraint(
                fields=['street1', 'street2', 'zip', 'city'],
                name='unique_address'
            )
        ]

    def __str__(self):
        """For representation in the Admin UI."""
        return f'{self.street1} {self.street2}, {self.zip} {self.city}'


class Site(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name='sites')
    responsible = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sites')
    nodes = models.ManyToManyField(Node, through='NodeInstallation')

    class Meta:
        constraints = [
            # The sites of a given user must be unique.
            models.UniqueConstraint(
                fields=['name', 'responsible'],
                name='unique_site_per_user'
            )
        ]

    def __str__(self):
        """For representation in the Admin UI."""
        return f'{self.name} {self.address.street1}, {self.address.zip}'


class NodeInstallation(models.Model):
    node = models.ForeignKey(
        Node, null=False, on_delete=models.CASCADE, related_name='node_installations')
    site = models.ForeignKey(
        Site, null=False, on_delete=models.CASCADE, related_name='node_installations')
    from_timestamp = models.PositiveIntegerField(null=False, blank=False)
    # An ongoing association does not have an end timestamp set.
    to_timestamp = models.PositiveIntegerField(null=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            # At any given time, a node may be attributed to one site only.
            models.UniqueConstraint(
                fields=['node', 'from_timestamp'],
                name='unique_node_attribution'
            )
        ]
        ordering = ['-from_timestamp']
        get_latest_by = 'from_timestamp'

    def __str__(self):
        """For representation in the Admin UI."""
        return f'Node: {self.node}, from: {datetime.utcfromtimestamp(self.from_timestamp)} To: {datetime.utcfromtimestamp(self.to_timestamp) if self.to_timestamp != None else "ongoing"}'
