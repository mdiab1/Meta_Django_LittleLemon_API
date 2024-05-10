from rest_framework import permissions

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Managers").exists()
    
class IsDelCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Delivery_Crew").exists()