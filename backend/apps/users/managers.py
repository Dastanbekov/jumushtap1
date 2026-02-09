"""
Custom User Manager for JumushTap
"""

from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where phone is the unique identifier for authentication.
    """
    
    def create_user(self, phone, user_type, password=None, **extra_fields):
        """
        Create and save a regular user with phone number.
        Note: Password is optional in MVP (using SMS OTP).
        """
        if not phone:
            raise ValueError('Phone number must be provided')
        if not user_type:
            raise ValueError('User type must be specified')
        
        user = self.model(
            phone=phone,
            user_type=user_type,
            **extra_fields
        )
        
        # Password is optional for OTP-based auth
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, user_type='admin', password=None, **extra_fields):
        """
        Create and save a superuser with phone number.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone, user_type, password, **extra_fields)