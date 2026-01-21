from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView, 
    UserProfileView, 
    ProfileUpdateView, 
    VerificationRequestView
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('users/me/', UserProfileView.as_view(), name='user_profile'),
    
    # Extended Profile (KYC/KYB)
    path('users/me/extended/', ProfileUpdateView.as_view(), name='extended_profile'),
    path('users/me/verify/', VerificationRequestView.as_view(), name='verify_profile'),
]
