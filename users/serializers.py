from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate


class UserSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'role'] # Specify desired output fields
        read_only_fields = fields
        
class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    agency_pan = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'full_name', 'contact', 'role', 'agency_pan')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data.get('role') == 'agency' and not data.get('agency_pan'):
            raise serializers.ValidationError("Agency PAN is required for agency accounts")
        if data.get('role') != 'agency' and data.get('agency_pan'):
            raise serializers.ValidationError("PAN number is only allowed for agency accounts")
        return data
    
class VerifyUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        if not email or not otp:
            raise serializers.ValidationError("Email and OTP are required")
        return data
    

# --- Serializer for Updating Basic Profile Info ---
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating basic user profile fields like name and contact.
    Agency PAN is included but needs careful validation in the view based on role.
    """
    # Make fields optional for PATCH requests
    full_name = serializers.CharField(max_length=255, required=False)
    contact = serializers.CharField(max_length=15, required=False)
    agency_pan = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CustomUser
        # Fields allowed to be updated via this serializer
        fields = ('full_name', 'contact', 'agency_pan')
        # Note: Role and Email are intentionally excluded - typically not changed here.

# --- Serializer for Updating Location Info ---
class UserLocationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for updating user location fields.
    """
    # Make fields optional for PATCH requests
    state = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    lat = serializers.FloatField(required=False, allow_null=True)
    long = serializers.FloatField(required=False, allow_null=True) # Match model field name 'long'

    class Meta:
        model = CustomUser
        fields = ('state', 'city', 'lat', 'long')

# --- Serializer for Displaying User Details (Used in Responses) ---
class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying detailed user information.
    """
    class Meta:
        model = CustomUser
        # List fields to include in the response after update/retrieval
        fields = (
            'id', 'email', 'full_name', 'contact', 'role', 'agency_pan',
            'is_verified', 'is_active', 'date_joined',
            'state', 'city', 'lat', 'long'
        )
        read_only_fields = fields # Ensure it's only used for output