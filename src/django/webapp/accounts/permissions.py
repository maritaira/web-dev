from rest_framework.permissions import BasePermission

class IsRaceOwner(BasePermission):
    """Allow only RaceOwners to create races and generate join codes."""

    def has_permission(self, request, view):
        print("In isRaceOwner has_permissions()")
        print(f"Groups: {request.user.groups}")
        return 'raceowner' in request.user.groups



class IsCarOwner(BasePermission):
    """Allow only CarOwners to join races."""

    def has_permission(self, request, view):
        print("In isCarOwner has_permissions()")
        print(f"Groups: {request.user.groups}")
        return 'carowner' in request.user.groups