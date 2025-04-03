from rest_framework import serializers
from .models import ExistingAgencies
from .models import MissingPersonReport
from .models import Event
from .models import TimelineItem
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


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
        
class TimelineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineItem
        fields = ['id', 'time', 'activity']

class EventSerializer(serializers.ModelSerializer):
    # Serialize the timeline items
    timeline_items = TimelineItemSerializer(many=True, read_only=False)
    user_id = serializers.IntegerField(write_only=True)  # Accept user_id in request

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'date', 'start_time', 'event_type', 'platform', 'meeting_link', 
            'meeting_id', 'venue_name', 'address', 'city', 'state', 'attendees', 
            'reg_type', 'tags', 'description', 'location_type', 'timeline_items', 'user_id'
        ]

    def create(self, validated_data):
        # Get the user_id from the request data and use it to link the event to the user
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)  # Get the user from the user_id
        event = Event.objects.create(user=user, **validated_data)  # Create the event and link to the user

        # Now handle timeline items
        timeline_items_data = validated_data.pop('timeline_items', [])
        for item_data in timeline_items_data:
            TimelineItem.objects.create(event=event, **item_data)  # Create timeline items

        return event

    def update(self, instance, validated_data):
        # Get the user_id and associate it with the event
        user_id = validated_data.pop('user_id', None)
        if user_id:
            user = User.objects.get(id=user_id)
            instance.user = user

        # Update other event fields
        instance.name = validated_data.get('name', instance.name)
        instance.date = validated_data.get('date', instance.date)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.event_type = validated_data.get('event_type', instance.event_type)
        instance.platform = validated_data.get('platform', instance.platform)
        instance.meeting_link = validated_data.get('meeting_link', instance.meeting_link)
        instance.meeting_id = validated_data.get('meeting_id', instance.meeting_id)
        instance.venue_name = validated_data.get('venue_name', instance.venue_name)
        instance.address = validated_data.get('address', instance.address)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.attendees = validated_data.get('attendees', instance.attendees)
        instance.reg_type = validated_data.get('reg_type', instance.reg_type)
        instance.tags = validated_data.get('tags', instance.tags)
        instance.description = validated_data.get('description', instance.description)
        instance.location_type = validated_data.get('location_type', instance.location_type)

        instance.save()

        # Handle timeline items (create or update)
        existing_timeline_items = {item.id: item for item in instance.timeline_items.all()}
        timeline_items_data = validated_data.pop('timeline_items', [])
        for item_data in timeline_items_data:
            item_id = item_data.get('id', None)
            if item_id and item_id in existing_timeline_items:
                item = existing_timeline_items[item_id]
                item.time = item_data.get('time', item.time)
                item.activity = item_data.get('activity', item.activity)
                item.save()
            else:
                TimelineItem.objects.create(event=instance, **item_data)

        return instance