from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class OTPStorage(models.Model):
    """Stores OTPs temporarily in the database."""
    email = models.EmailField(unique=True, help_text="Email address the OTP was sent to.")
    otp = models.CharField(max_length=6, help_text="The 6-digit OTP.")
    # Store when the OTP expires
    expires_at = models.DateTimeField(help_text="Timestamp when this OTP will expire.")
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        """Check if the OTP has expired."""
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"OTP for {self.email} (Expires: {self.expires_at})"

    class Meta:
        verbose_name = "OTP Storage"
        verbose_name_plural = "OTP Storage"

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
    # Add related_name to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )
    
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