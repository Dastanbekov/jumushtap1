"""
URL Configuration for Users app.
SMS OTP-based authentication endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    SendOTPView,
    VerifyOTPView,
    RegisterWorkerView,
    RegisterBusinessView,
    UserMeView,
    UpdateWorkerProfileView,
    UpdateBusinessProfileView,
)

app_name = 'users'

urlpatterns = [
    # OTP Authentication
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    # Registration (OTP + Profile creation)
    path('register/worker/', RegisterWorkerView.as_view(), name='register-worker'),
    path('register/business/', RegisterBusinessView.as_view(), name='register-business'),
    
    # JWT Token Refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Profile Management
    path('me/', UserMeView.as_view(), name='me'),
    path('profile/worker/', UpdateWorkerProfileView.as_view(), name='update-worker-profile'),
    path('profile/business/', UpdateBusinessProfileView.as_view(), name='update-business-profile'),
]