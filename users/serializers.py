from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate


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