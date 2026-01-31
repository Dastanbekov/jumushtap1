from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, WorkerProfileSerializer,BusinessProfileSerializer,IndividualProfileSerializer

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken # <-- Импортируем это
from .serializers import UserRegistrationSerializer

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # --- ГЕНЕРАЦИЯ ТОКЕНОВ ---
        # Создаем токены вручную для нового юзера
        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_type": user.user_type, # Полезно вернуть роль сразу
            "message": "User registered and logged in successfully"
        }, status=status.HTTP_201_CREATED)

# Для логина используем стандартный SimpleJWT View, но можно его кастомизировать
class CustomTokenObtainPairView(TokenObtainPairView):
    # Здесь можно добавить кастомный сериалайзер, если нужно возвращать еще и роль юзера вместе с токеном
    pass

class UserMeView(APIView):
    """
    Возвращает данные текущего залогиненного пользователя
    и его профиля в зависимости от роли.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "email": user.email,
            "phone": str(user.phone),
            "user_type": user.user_type,
        }

        # Подмешиваем данные профиля
        try:
            if user.user_type == 'worker':
                data.update(WorkerProfileSerializer(user.worker_profile).data)
            elif user.user_type == 'business':
                data.update(BusinessProfileSerializer(user.business_profile).data)
            elif user.user_type == 'individual':
                data.update(IndividualProfileSerializer(user.individual_profile).data)
        except Exception as e:
            # На случай, если юзер есть, а профиль почему-то не создался (баг)
            data['profile_error'] = "Profile not found"

        return Response(data)