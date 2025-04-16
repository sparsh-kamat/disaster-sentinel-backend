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
    
