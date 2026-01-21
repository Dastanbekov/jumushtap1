from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    WorkerProfileSerializer, 
    CustomerProfileSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Update extended profile data (Worker or Customer).
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        # Ensure profile exists (handled by signals mostly, but safe check)
        if user.role == 'worker':
            if not hasattr(user, 'worker_profile'):
                from .models import WorkerProfile
                WorkerProfile.objects.create(user=user)
            return user.worker_profile
        elif user.role == 'customer':
            if not hasattr(user, 'customer_profile'):
                from .models import CustomerProfile
                CustomerProfile.objects.create(user=user)
            return user.customer_profile
        return None 

    def get_serializer_class(self):
        user = self.request.user
        if user.role == 'worker':
            return WorkerProfileSerializer
        return CustomerProfileSerializer

class VerificationRequestView(APIView):
    """
    Submit profile for verification.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        profile = None
        if user.role == 'worker':
            profile = user.worker_profile
        elif user.role == 'customer':
            profile = user.customer_profile
        
        if profile:
            # Check logic can be added here (e.g. check if passport is uploaded)
            if profile.verification_status == 'verified':
                 return Response({'detail': 'Already verified'}, status=status.HTTP_400_BAD_REQUEST)
            
            profile.verification_status = 'pending'
            profile.save()
            return Response({'status': 'Verification request sent'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Profile not found'}, status=status.HTTP_400_BAD_REQUEST)
