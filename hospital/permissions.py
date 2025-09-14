from rest_framework import permissions

class IsRole(permissions.BasePermission):
    """
    Allow access only to users with one of the allowed roles.
    Pass a list like ['DOCTOR','NURSE'] into view as attribute `allowed_roles`.
    """

    def has_permission(self, request, view):
        allowed = getattr(view, 'allowed_roles', None)
        if allowed is None:
            return True
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
        return profile.role in allowed
