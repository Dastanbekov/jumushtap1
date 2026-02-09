"""
Views for User authentication and profile management.
Implements SMS OTP-based authentication per MVP specifications.
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    WorkerRegistrationSerializer,
    BusinessRegistrationSerializer,
    UserProfileSerializer,
    WorkerProfileSerializer,
    BusinessProfileSerializer,
)
from .services import OTPService, UserService
from .models import UserType
from core.permissions import IsWorker, IsBusiness

logger = logging.getLogger(__name__)


class SendOTPView(APIView):
    """
    POST /api/v1/auth/send-otp/
    
    Request OTP code to be sent via SMS.
    Rate limited to prevent abuse.
    
    Request Body:
    {
        "phone": "+996700123456"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP sent successfully"
    }
    """
    permission_classes = [AllowAny]
    
    @method_decorator(never_cache)
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone = serializer.validated_data['phone']
        
        # Send OTP via service
        success, message, otp_id = OTPService.send_otp(phone)
        
        if success:
            return Response({
                'success': True,
                'message': message,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS if 'many' in message.lower() else status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    POST /api/v1/auth/verify-otp/
    
    Verify OTP code and get JWT tokens.
    If user doesn't have a complete profile, returns profile_incomplete flag.
    
    Request Body:
    {
        "phone": "+996700123456",
        "code": "123456"
    }
    
    Response (successful):
    {
        "success": true,
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user_type": "worker",
        "profile_complete": true/false
    }
    """
    permission_classes = [AllowAny]
    
    @method_decorator(never_cache)
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        
        # Verify OTP
        success, message, user = OTPService.verify_otp(phone, code)
        
        if not success:
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate JWT tokens
        tokens = UserService.generate_tokens_for_user(user)
        
        # Check if profile is complete
        profile_complete = False
        try:
            if user.user_type == UserType.WORKER:
                profile_complete = hasattr(user, 'worker_profile')
            elif user.user_type == UserType.BUSINESS:
                profile_complete = hasattr(user, 'business_profile')
        except Exception:
            pass
        
        return Response({
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user_type': user.user_type,
            'profile_complete': profile_complete,
        }, status=status.HTTP_200_OK)


class RegisterWorkerView(APIView):
    """
    POST /api/v1/auth/register/worker/
    
    Complete worker profile after OTP verification.
    This combines OTP verification + profile creation.
    
    Request Body:
    {
        "phone": "+996700123456",
        "code": "123456",
        "profile": {
            "full_name": "John Doe",
            "skills": ["waiter", "courier"],
            "experience": "2 years experience..."
        }
    }
    
    Response:
    {
        "success": true,
        "access": "jwt_token",
        "refresh": "jwt_refresh_token",
        "user": {...}
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = WorkerRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create/update profile
        result = serializer.save()
        user = result['user']
        
        # Generate tokens
        tokens = UserService.generate_tokens_for_user(user)
        
        # Get profile data
        profile_data = UserService.get_user_profile_data(user)
        
        return Response({
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': profile_data,
            'message': 'Worker profile created successfully',
        }, status=status.HTTP_201_CREATED)


class RegisterBusinessView(APIView):
    """
    POST /api/v1/auth/register/business/
    
    Complete business profile after OTP verification.
    
    Request Body:
    {
        "phone": "+996700123456",
        "code": "123456",
        "profile": {
            "company_name": "Tech LLC",
            "bin": "123456789012",
            "inn": "12345678901234",
            "legal_address": "Bishkek, Chuy 1",
            "contact_name": "Manager",
            "contact_number": "+996555123456",
            "locations": []
        }
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = BusinessRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create/update profile
        result = serializer.save()
        user = result['user']
        
        # Generate tokens
        tokens = UserService.generate_tokens_for_user(user)
        
        # Get profile data
        profile_data = UserService.get_user_profile_data(user)
        
        return Response({
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': profile_data,
            'message': 'Business profile created successfully. Verification pending.',
        }, status=status.HTTP_201_CREATED)


class UserMeView(APIView):
    """
    GET /api/v1/auth/me/
    
    Get current authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class UpdateWorkerProfileView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/v1/auth/profile/worker/
    
    Update worker profile (own profile only).
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [IsAuthenticated, IsWorker]
    
    def get_object(self):
        return self.request.user.worker_profile
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        logger.info(f"Worker profile updated for user {request.user.phone}")
        return response


class UpdateBusinessProfileView(generics.UpdateAPIView):
    """
    PUT/PATCH /api/v1/auth/profile/business/
    
    Update business profile (own profile only).
    """
    serializer_class = BusinessProfileSerializer
    permission_classes = [IsAuthenticated, IsBusiness]
    
    def get_object(self):
        return self.request.user.business_profile
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        logger.info(f"Business profile updated for user {request.user.phone}")
        return response