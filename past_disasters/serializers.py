from rest_framework import serializers
from .models import PastDisaster

class PastDisasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastDisaster
        fields = '__all__'  # This will include all fields in the model
