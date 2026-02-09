"""
Serializers for User authentication and profiles.
Follows MVP specifications with phone + OTP authentication.
"""

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from .models import CustomUser, WorkerProfile, BusinessProfile, UserType, VerificationStatus
from .services import OTPService, UserService


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP code.
    """
    phone = PhoneNumberField(required=True, help_text="Phone number in international format")
    
    def validate_phone(self, value):
        """Validate phone number format."""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        return value


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    """
    phone = PhoneNumberField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    
    def validate_code(self, value):
        """Validate OTP code format."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits")
        return value


class WorkerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Worker Profile.
    MVP fields only.
    """
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkerProfile
        fields = [
            'full_name',
            'date_of_birth',
            'photo',
            'photo_url',
            'skills',
            'experience',
            'rating',
            'completed_jobs_count',
            'verification_status',
            'payment_account_id',
        ]
        read_only_fields = ['rating', 'completed_jobs_count', 'verification_status']
    
    def get_photo_url(self, obj):
        """Get absolute URL for photo."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def validate_skills(self, value):
        """Validate skills array."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be an array")
        return value


class BusinessProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Business Profile.
    MVP fields only.
    """
    class Meta:
        model = BusinessProfile
        fields = [
            'company_name',
            'bin',
            'inn',
            'legal_address',
            'contact_name',
            'contact_number',
            'documents',
            'locations',
            'verification_status',
        ]
        read_only_fields = ['verification_status']
    
    def validate_documents(self, value):
        """Validate documents array structure."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Documents must be an array")
        
        for doc in value:
            if not isinstance(doc, dict):
                raise serializers.ValidationError("Each document must be an object")
            if 'type' not in doc or 'url' not in doc:
                raise serializers.ValidationError("Each document must have 'type' and 'url' fields")
        
        return value
    
    def validate_locations(self, value):
        """Validate locations array structure."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Locations must be an array")
        
        for loc in value:
            if not isinstance(loc, dict):
                raise serializers.ValidationError("Each location must be an object")
            required_fields = ['address', 'lat', 'lng']
            if not all(field in loc for field in required_fields):
                raise serializers.ValidationError(
                    f"Each location must have: {', '.join(required_fields)}"
                )
        
        return value


class WorkerRegistrationSerializer(serializers.Serializer):
    """
    Serializer for worker registration (after OTP verification).
    """
    phone = PhoneNumberField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    profile = WorkerProfileSerializer(required=True)
    
    def validate(self, data):
        """Verify OTP and prepare for registration."""
        # Verify OTP
        phone = data['phone']
        code = data['code']
        
        success, message, user = OTPService.verify_otp(phone, code)
        
        if not success:
            raise serializers.ValidationError({'code': message})
        
        # Store verified user in context for create() method
        self.context['verified_user'] = user
        
        return data
    
    def create(self, validated_data):
        """
        Complete worker registration.
        """
        user = self.context['verified_user']
        profile_data = validated_data['profile']
        
        # Create/update profile
        profile = UserService.complete_worker_registration(user, profile_data)
        
        return {
            'user': user,
            'profile': profile,
        }


class BusinessRegistrationSerializer(serializers.Serializer):
    """
    Serializer for business registration (after OTP verification).
    """
    phone = PhoneNumberField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    profile = BusinessProfileSerializer(required=True)
    
    def validate(self, data):
        """Verify OTP and prepare for registration."""
        # Verify OTP
        phone = data['phone']
        code = data['code']
        
        success, message, user = OTPService.verify_otp(phone, code)
        
        if not success:
            raise serializers.ValidationError({'code': message})
        
        # Store verified user in context
        self.context['verified_user'] = user
        
        return data
    
    def create(self, validated_data):
        """
        Complete business registration.
        """
        user = self.context['verified_user']
        profile_data = validated_data['profile']
        
        # Create/update profile
        profile = UserService.complete_business_registration(user, profile_data)
        
        return {
            'user': user,
            'profile': profile,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read-only, for /me endpoint).
    """
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'phone', 'user_type', 'date_joined', 'profile']
        read_only_fields = fields
    
    def get_profile(self, obj):
        """Get profile data based on user type."""
        try:
            if obj.user_type == UserType.WORKER:
                profile = obj.worker_profile
                return WorkerProfileSerializer(profile, context=self.context).data
            
            elif obj.user_type == UserType.BUSINESS:
                profile = obj.business_profile
                return BusinessProfileSerializer(profile, context=self.context).data
            
        except (WorkerProfile.DoesNotExist, BusinessProfile.DoesNotExist):
            return {'incomplete': True}
        
        return None