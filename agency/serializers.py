from rest_framework import serializers
from .models import ExistingAgencies

class ExistingAgenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExistingAgencies
        fields = '__all__'  # This will include all fields in the model
        
