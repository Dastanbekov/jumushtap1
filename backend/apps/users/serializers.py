from rest_framework import serializers
from django.db import transaction
from .models import CustomUser, WorkerProfile, BusinessProfile, IndividualProfile, UserType

# 1. Сериалайзеры для профилей
class WorkerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerProfile
        fields = ['full_name']

class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = ['company_name', 'bin', 'inn', 'legal_address', 'contact_name', 'contact_number']

class IndividualProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndividualProfile
        fields = ['full_name_ru']

# 2. Главный Сериалайзер Регистрации
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # Это поле будет принимать JSON с данными профиля
    profile = serializers.DictField(write_only=True) 

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'phone', 'user_type', 'profile']

    def validate(self, data):
        """
        Проверяем, что данные профиля соответствуют выбранному типу
        """
        user_type = data.get('user_type')
        profile_data = data.get('profile')
        
        if user_type == UserType.WORKER:
            serializer = WorkerProfileSerializer(data=profile_data)
        elif user_type == UserType.BUSINESS:
            serializer = BusinessProfileSerializer(data=profile_data)
        elif user_type == UserType.INDIVIDUAL:
            serializer = IndividualProfileSerializer(data=profile_data)
        else:
            raise serializers.ValidationError("Invalid user type")
        
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        
        # Сохраняем валидированные данные профиля во временное хранилище (context)
        self.context['profile_valid_data'] = serializer.validated_data
        return data

    def create(self, validated_data):
        """
        Атомарное создание User + Profile
        """
        profile_data = self.context['profile_valid_data']
        # Убираем profile из данных для юзера, так как это не поле модели User
        validated_data.pop('profile') 
        password = validated_data.pop('password')
        
        with transaction.atomic():
            # 1. Создаем User
            user = CustomUser.objects.create_user(password=password, **validated_data)
            
            # 2. Создаем Profile в зависимости от типа
            if user.user_type == UserType.WORKER:
                WorkerProfile.objects.create(user=user, **profile_data)
            elif user.user_type == UserType.BUSINESS:
                BusinessProfile.objects.create(user=user, **profile_data)
            elif user.user_type == UserType.INDIVIDUAL:
                IndividualProfile.objects.create(user=user, **profile_data)
                
            return user