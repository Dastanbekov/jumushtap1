# apps/users/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] # Разрешить всем регистрироваться

    def create(self, request, *args, **kwargs):
        # Переопределяем create, чтобы вернуть красивый ответ без пароля
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user_id": user.id,
            "email": user.email,
            "message": "User created successfully. Now you can login."
        }, status=status.HTTP_201_CREATED)

# Для логина используем стандартный SimpleJWT View, но можно его кастомизировать
class CustomTokenObtainPairView(TokenObtainPairView):
    # Здесь можно добавить кастомный сериалайзер, если нужно возвращать еще и роль юзера вместе с токеном
    pass