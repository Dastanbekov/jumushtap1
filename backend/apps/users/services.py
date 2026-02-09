"""
Services for User authentication and profile management.
Implements business logic following Clean Architecture principles.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.cache import cache

from .models import CustomUser, OTP, WorkerProfile, BusinessProfile, UserType, VerificationStatus
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


class OTPService:
    """
    Service for SMS OTP generation and verification.
    Implements rate limiting and security best practices.
    """
    
    OTP_EXPIRY_MINUTES = 5
    MAX_OTP_ATTEMPTS = 3
    OTP_RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    
    @classmethod
    def send_otp(cls, phone):
        """
        Generate and send OTP code to phone number.
        
        Args:
            phone: PhoneNumber object
        
        Returns:
            tuple: (success: bool, message: str, otp_id: int or None)
        
        Raises:
            Exception: If SMS sending fails
       """
        # Rate limiting check
        rate_limit_key = f"otp_sent:{phone}"
        sent_count = cache.get(rate_limit_key, 0)
       
        if sent_count >= 3:  # Max 3 OTPs per hour
            logger.warning(f"OTP rate limit exceeded for {phone}")
            return False, "Too many OTP requests. Please try again later.", None
        
        # Generate new OTP
        code = OTP.generate_code()
        expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
        
        try:
            # Save OTP to database
            with transaction.atomic():
                # Invalidate previous OTPs for this phone
                OTP.objects.filter(
                    phone=phone,
                    is_used=False
                ).update(is_used=True)
                
                # Create new OTP
                otp = OTP.objects.create(
                    phone=phone,
                    code=code,
                    expires_at=expires_at
                )
                
                # Send SMS
                cls._send_sms(phone, code)
                
                # Update rate limit counter
                cache.set(rate_limit_key, sent_count + 1, cls.OTP_RATE_LIMIT_WINDOW)
                
                logger.info(f"OTP sent successfully to {phone}")
                return True, "OTP sent successfully", otp.id
                
        except Exception as e:
            logger.error(f"Failed to send OTP to {phone}: {e}", exc_info=True)
            return False, "Failed to send OTP. Please try again.", None
    
    @classmethod
    def verify_otp(cls, phone, code):
        """
        Verify OTP code for phone number.
        
        Args:
            phone: PhoneNumber object
            code: str - 6-digit OTP code
        
        Returns:
            tuple: (success: bool, message: str, user: CustomUser or None)
        """
        try:
            # Get latest unused OTP for this phone
            otp = OTP.objects.filter(
                phone=phone,
                code=code,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp:
                logger.warning(f"Invalid OTP attempt for {phone}")
                return False, "Invalid OTP code", None
            
            # Check if expired
            if not otp.is_valid():
                logger.warning(f"Expired OTP used for {phone}")
                return False, "OTP has expired. Please request a new one.", None
            
            # Mark as used
            otp.mark_as_used()
            
            # Get or create user
            user = cls._get_or_create_user(phone)
            
            logger.info(f"OTP verified successfully for {phone}")
            return True, "OTP verified successfully", user
            
        except Exception as e:
            logger.error(f"OTP verification error for {phone}: {e}", exc_info=True)
            return False, "Verification failed. Please try again.", None
    
    @staticmethod
    def _send_sms(phone, code):
        """
        Send SMS via configured provider.
        Supports: console (dev), twilio (production).
        """
        from django.conf import settings
        
        sms_provider = getattr(settings, 'SMS_PROVIDER', 'console')
        message = f"Your JumushTap verification code is: {code}. Valid for 5 minutes."
        
        if sms_provider == 'console':
            # Development: print to console
            print(f"\n{'='*50}")
            print(f"📱 SMS to {phone}")
            print(f"Message: {message}")
            print(f"{'='*50}\n")
            logger.info(f"SMS (console): {phone} - {code}")
            
        elif sms_provider == 'twilio':
            # Production: send via Twilio
            from twilio.rest import Client
            
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            from_number = settings.TWILIO_PHONE_NUMBER
            
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_number,
                to=str(phone)
            )
            logger.info(f"SMS sent via Twilio to {phone}")
        
        else:
            # Local/custom provider (implement as needed)
            logger.warning(f"Unknown SMS provider: {sms_provider}")
            print(f"SMS Code for {phone}: {code}")
    
    @staticmethod
    def _get_or_create_user(phone):
        """
        Get existing user or create placeholder.
        Full profile will be completed after OTP verification.
        """
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={'user_type': UserType.WORKER}  # Default, can be changed during registration
        )
        
        if created:
            logger.info(f"New user created for {phone}")
        
        return user


class UserService:
    """
    Service for user profile management and registration.
    """
    
    @staticmethod
    @transaction.atomic
    def complete_worker_registration(user, profile_data):
        """
        Complete worker profile after OTP verification.
        
        Args:
            user: CustomUser instance
            profile_data: dict with worker profile fields
        
        Returns:
            WorkerProfile instance
        """
        # Update user type if needed
        if user.user_type != UserType.WORKER:
            user.user_type = UserType.WORKER
            user.save(update_fields=['user_type'])
        
        # Create or update worker profile
        profile, created = WorkerProfile.objects.update_or_create(
            user=user,
            defaults=profile_data
        )
        
        logger.info(f"Worker profile {'created' if created else 'updated'} for {user.phone}")
        return profile
    
    @staticmethod
    @transaction.atomic
    def complete_business_registration(user, profile_data):
        """
        Complete business profile after OTP verification.
        
        Args:
            user: CustomUser instance
            profile_data: dict with business profile fields
        
        Returns:
            BusinessProfile instance
        """
        # Update user type if needed
        if user.user_type != UserType.BUSINESS:
            user.user_type = UserType.BUSINESS
            user.save(update_fields=['user_type'])
        
        # Create or update business profile
        profile, created = BusinessProfile.objects.update_or_create(
            user=user,
            defaults=profile_data
        )
        
        logger.info(f"Business profile {'created' if created else 'updated'} for {user.phone}")
        return profile
    
    @staticmethod
    def generate_tokens_for_user(user):
        """
        Generate JWT tokens for authenticated user.
        
        Returns:
            dict: {'refresh': str, 'access': str}
        """
        refresh = RefreshToken.for_user(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    @staticmethod
    def get_user_profile_data(user):
        """
        Get complete profile data for user.
        
        Returns:
            dict with user and profile data
        """
        data = {
            'id': user.id,
            'phone': str(user.phone),
            'user_type': user.user_type,
            'date_joined': user.date_joined.isoformat(),
        }
        
        try:
            if user.user_type == UserType.WORKER:
                profile = user.worker_profile
                data.update({
                    'full_name': profile.full_name,
                    'photo': profile.photo.url if profile.photo else None,
                    'skills': profile.skills,
                    'experience': profile.experience,
                    'rating': float(profile.rating),
                    'completed_jobs_count': profile.completed_jobs_count,
                    'verification_status': profile.verification_status,
                })
                
            elif user.user_type == UserType.BUSINESS:
                profile = user.business_profile
                data.update({
                    'company_name': profile.company_name,
                    'bin': profile.bin,
                    'inn': profile.inn,
                    'legal_address': profile.legal_address,
                    'contact_name': profile.contact_name,
                    'contact_number': str(profile.contact_number),
                    'locations': profile.locations,
                    'verification_status': profile.verification_status,
                })
        
        except (WorkerProfile.DoesNotExist, BusinessProfile.DoesNotExist):
            data['profile_incomplete'] = True
        
        return data
