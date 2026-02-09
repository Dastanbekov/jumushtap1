"""
Permissions for Jobs app.
"""

from rest_framework import permissions


class IsJobOwner(permissions.BasePermission):
    """
    Permission to check if user owns the job.
    """
    message = "You don't have permission to modify this job."
    
    def has_object_permission(self, request, view, obj):
        # Safe methods (GET, HEAD, OPTIONS) allowed for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check ownership
        return obj.business == request.user


class IsApplicationOwner(permissions.BasePermission):
    """
    Permission for application owner (worker).
    """
    message = "You don't have permission to access this application."
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user


class IsJobOwnerOrApplicationOwner(permissions.BasePermission):
    """
    Permission for job owner OR application owner.
    Used for viewing application details.
    """
    def has_object_permission(self, request, view, obj):
        return (
            obj.job.business == request.user or
            obj.worker == request.user
        )


class CanApplyToJobs(permissions.BasePermission):
    """
    Check if user can apply to jobs (must be verified worker).
    """
    message = "Only verified workers can apply to jobs."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.user_type != 'worker':
            return False
        
        try:
            profile = request.user.worker_profile
            return profile.verification_status == 'verified'
        except AttributeError:
            return False
