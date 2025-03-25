from rest_framework.permissions import BasePermission

class IsRaceOwner(BasePermission):
    """Allow only RaceOwners to create races and generate join codes."""

    def has_permission(self, request, view):
        return request.user.groups.filter(name="raceowner").exists()


class IsCarOwner(BasePermission):
    """Allow only CarOwners to join races."""

    def has_permission(self, request, view):
        return request.user.groups.filter(name="carowner").exists()