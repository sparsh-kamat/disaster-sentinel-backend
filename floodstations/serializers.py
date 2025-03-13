from rest_framework import serializers
from .models import FloodInformation, StationInformation

class StationInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationInformation
        fields = '__all__'

class FloodInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloodInformation
        fields = '__all__'