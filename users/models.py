from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError


# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agency', 'Agency')
    ]
    
    # Remove username field
    username = None
    # Add custom fields
    full_name = models.CharField(max_length=255)
    contact = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    agency_pan = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    id = models.AutoField(primary_key=True)
    
    #location fields , will be added by later not at registration
    
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    long = models.FloatField(blank=True, null=True)
    
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'contact', 'role']
    
    objects = CustomUserManager()

    def clean(self):
        super().clean()
        if self.role == 'agency' and not self.agency_pan:
            raise ValidationError({'agency_pan': 'Agency PAN is required for agency accounts'})
        if self.role != 'agency' and self.agency_pan:
            raise ValidationError({'agency_pan': 'PAN number is only allowed for agency accounts'})

    def __str__(self):
        return self.email