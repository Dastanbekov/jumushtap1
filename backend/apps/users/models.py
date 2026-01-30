from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from .managers import CustomUserManager # Этот файл создадим ниже

class UserType(models.TextChoices):
    WORKER = 'worker', _('Worker')
    BUSINESS = 'business', _('Business')
    INDIVIDUAL = 'individual', _('Individual')

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    # Используем PhoneNumberField для автоматической валидации формата (+996...)
    phone = PhoneNumberField(unique=True, null=True, blank=True) 
    user_type = models.CharField(max_length=20, choices=UserType.choices)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email и так required

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# --- Profiles ---

class WorkerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='worker_profile')
    full_name = models.CharField(max_length=255)
    # Phone и Email уже есть в User, дублировать не обязательно, если они совпадают

    def __str__(self):
        return f"Worker: {self.full_name}"

class BusinessProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=255)
    bin = models.CharField(max_length=20, unique=True) # БИН
    inn = models.CharField(max_length=20, unique=True) # ИНН
    legal_address = models.TextField()
    contact_name = models.CharField(max_length=255)
    contact_number = PhoneNumberField() # Контактный номер может отличаться от номера логина
    # Email уже есть в user

    def __str__(self):
        return f"Business: {self.company_name}"

class IndividualProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='individual_profile')
    full_name_ru = models.CharField(max_length=255, verbose_name="ФИО")
    # Phone и Email в User

    def __str__(self):
        return f"Individual: {self.full_name_ru}"