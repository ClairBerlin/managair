from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed

from core.models import Membership


class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission that allows only the OWNERS of an organization to add, modify or delete a node owned by this orgnization.
    """

    @classmethod
    def has_create_permission(cls, request, serializer):
        """Authorize a new resource to be created.

        This is not an overwritten BasePermission method, but a custom method necessary for our access policy that depends on the incoming resource.

        This method must be called after deserialization and validation of the incoming request data to prevent injection attacks. To my understanding, the only place to do so on a generic viewset is in the `perform_create()` method. Thus: Overwrite `perform_create()` on your viewset and call the present method there.
        """
        if request.method == "POST":
            # Is the authorized user an OWNER of the organization to which the resource
            # is to be added?

            owner = serializer.get_owner()
            try:
                membership = request.user.memberships.get(organization__id=owner.id)
            except Membership.DoesNotExist:
                raise PermissionDenied
            return membership.isOwner()
        else:
            # Should never happen.
            raise MethodNotAllowed(request.method)

    def has_object_permission(self, request, view, obj):
        """Permissions at the object-level are important for existing nodes."""

        if request.method in ["PUT", "PATCH", "DELETE"]:
            # Is the authorized user an OWNER of the organization that owns the resource
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