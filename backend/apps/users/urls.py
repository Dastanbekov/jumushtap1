# apps/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserRegistrationView, CustomTokenObtainPairView,UserMeView

urlpatterns = [
	path('me/', UserMeView.as_view(), name='users-me'),

    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # JWT Login
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]