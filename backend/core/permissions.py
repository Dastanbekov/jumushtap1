"""
Global Permissions for JumushTap
Enterprise-grade RBAC + Object-level access control.
"""

from rest_framework import permissions


class IsWorker(permissions.BasePermission):
    """
    Permission to check if user is a Worker.
    """
    message = 'This action requires Worker role.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'worker'
        )


class IsBusiness(permissions.BasePermission):
    """
    Permission to check if user is a Business.
    """
    message = 'This action requires Business role.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'business'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is an Admin.
    """
    message = 'This action requires Administrator role.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    
    Assumes the object has a 'user' field or 'business' field.
    Critical for preventing BOLA (Broken Object Level Authorization).
    """
    message = 'You do not have permission to access this resource.'
    
    def has_object_permission(self, request, view, obj):
        # Check if object has 'user' field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object has 'business' field  
        if hasattr(obj, 'business'):
            return obj.business == request.user
        
        # Check if object has 'worker' field
        if hasattr(obj, 'worker'):
            return obj.worker == request.user
        
        # Default deny
        return False


class IsVerifiedWorker(permissions.BasePermission):
    """
    Permission to check if user is a verified Worker.
    Prevents unverified workers from applying to jobs.
    """
    message = 'Your worker profile must be verified to perform this action.'
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.user_type != 'worker':
            return False
        
        # Check verification status
        try:
            profile = request.user.worker_profile
            return profile.verification_status == 'verified'
        except AttributeError:
            return False


class IsVerifiedBusiness(permissions.BasePermission):
    """
    Permission to check if user is a verified Business.
    Prevents unverified businesses from posting jobs.
    """
    message = 'Your business profile must be verified to perform this action.'
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.user_type != 'business':
            return False
        
        # Check verification status
        try:
            profile = request.user.business_profile
            return profile.verification_status == 'verified'
        except AttributeError:
            return False


class ReadOnly(permissions.BasePermission):
    """
    Permission to allow only GET, HEAD, OPTIONS requests.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: owner can edit, others can read.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'business'):
            return obj.business == request.user
        if hasattr(obj, 'worker'):
            return obj.worker == request.user
        
        return False
