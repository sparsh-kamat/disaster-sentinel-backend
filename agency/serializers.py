from rest_framework import serializers
from .models import ExistingAgencies
from .models import MissingPersonReport

class MissingPersonReportSerializer(serializers.ModelSerializer):
    person_photo_url = serializers.ImageField(source='person_photo', read_only=True)
    id_card_photo_url = serializers.ImageField(source='id_card_photo', read_only=True)

    class Meta:
        model = MissingPersonReport
        fields = [
            'id',
            'full_name',
            'last_seen_location',
            'identification_marks',
            'description',  # Added description field
            'person_photo_url',
            'id_card_photo_url',
            'has_id_card',
            'has_person_photo',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('reporter', 'has_id_card', 'has_person_photo')
        
        
class ExistingAgenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExistingAgencies
        fields = '__all__'  # This will include all fields in the model
        
