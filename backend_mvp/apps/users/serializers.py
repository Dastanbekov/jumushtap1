from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WorkerProfile, CustomerProfile, Skill

User = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')

class WorkerProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        many=True,
        write_only=True,
        source='skills'
    )

    class Meta:
        model = WorkerProfile
        exclude = ('user',)
        read_only_fields = ('verification_status', 'rejection_reason')


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        exclude = ('user',)
        read_only_fields = ('verification_status', 'rejection_reason')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role', 'phone', 'first_name', 'last_name')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'customer'),
            phone=validated_data.get('phone', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'phone', 
            'rating', 'status', 'first_name', 'last_name', 
            'is_verified', 'profile'
        )
        read_only_fields = ('id', 'rating', 'status', 'role', 'is_verified')

    def get_profile(self, obj):
        if obj.role == 'worker' and hasattr(obj, 'worker_profile'):
            return WorkerProfileSerializer(obj.worker_profile).data
        elif obj.role == 'customer' and hasattr(obj, 'customer_profile'):
            return CustomerProfileSerializer(obj.customer_profile).data
        return None
