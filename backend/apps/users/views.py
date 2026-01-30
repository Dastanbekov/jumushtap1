from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, APIView
from .serializers import UserRegistrationSerializer, WorkerProfileSerializer,BusinessProfileSerializer,IndividualProfileSerializer

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