from rest_framework import permissions

from .models import User


class IsRole(permissions.BasePermission):
    roles = ()

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.roles


class IsRecruiter(IsRole):
    roles = (User.RECRUITER,)


class IsCandidate(IsRole):
    roles = (User.CANDIDATE,)


class IsAdminRole(IsRole):
    roles = (User.ADMIN,)
