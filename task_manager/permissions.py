from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.owner == request.user


class CanGetStatisticPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('task_manager.can_get_statistic')