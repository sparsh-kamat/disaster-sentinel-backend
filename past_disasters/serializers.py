from rest_framework import serializers
from .models import PastDisaster
from past_disasters.models import GdacsDisasterEvent

class PastDisasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastDisaster
        fields = '__all__'  # This will include all fields in the model


class GdacsDisasterEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = GdacsDisasterEvent
        fields = '__all__'  # Include all fields of the model, or specify fields explicitly

from rest_framework import serializers
from .models import GdacsDisasterEvent

class GdacsDisasterEventTitleStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GdacsDisasterEvent
        fields = ['title', 'state']
