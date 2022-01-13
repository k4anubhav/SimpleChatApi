from rest_framework.permissions import BasePermission


class IsAuthAndNotBanned(BasePermission):
    """
    Allows access only to authenticated users that are not banned.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.banned)
