from rest_framework import serializers
from .models import ExistingAgencies
from .models import Event
from .models import VolunteerInterest
from .models import AgencyProfile
from .models import AgencyImage
from .models import EventInterest
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import AgencyMemberPermission

# --- Serializer for nested Member details ---
class MemberInfoSerializer(serializers.ModelSerializer):
    """Read-only serializer for basic member info."""
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'contact'] # Fields to display
        read_only = True

# --- Serializer for Displaying Permissions ---
class AgencyMemberPermissionDetailSerializer(serializers.ModelSerializer):
    """Displays permission details including nested member info."""
    # Use the nested serializer for the 'member' field
    member = MemberInfoSerializer(read_only=True)

    class Meta:
        model = AgencyMemberPermission
        # Include all fields from the model + the nested 'member'
        fields = [
            'agency', # Shows agency ID
            'member', # Shows nested member details
            'can_view_missing',
            'can_edit_missing',
            'can_view_announcements',
            'can_edit_announcements',
            'can_make_announcements',
            'can_manage_volunteers',
            'is_agency_admin',
            'granted_at',
            'updated_at'
        ]
        read_only_fields = fields # This serializer is for display only

# --- Serializer for Updating/Setting Permissions ---
class AgencyMemberPermissionUpdateSerializer(serializers.ModelSerializer):
    """Handles updating the boolean permission flags."""
    # All boolean fields are included by default from the model
    # They are optional for PATCH, required for PUT (unless default exists)

    class Meta:
        model = AgencyMemberPermission
        # Only include the permission flags that can be set/updated
        fields = [
            'can_view_missing',
            'can_edit_missing',
            'can_view_announcements',
            'can_edit_announcements',
            'can_make_announcements',
            'can_manage_volunteers',
            'is_agency_admin',
        ]
        # Exclude 'agency' and 'member' as they are determined by the URL/view
        # exclude = ['agency', 'member', 'granted_at', 'updated_at'] # Alternative
        
# --- Serializer for Image Details (Used for nesting) ---
class AgencyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at'] # Image can be replaced via update? Usually handled separately.

# --- Serializer for CREATING Agency Profile (No Auth) ---
class AgencyProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for CREATING AgencyProfile without authentication.
    Expects 'user_id' in the input data. Images handled via request.FILES.
    """
    user_id = serializers.IntegerField(
        write_only=True,
        required=True,
        help_text="The ID of the agency user this profile belongs to."
    )

    class Meta:
        model = AgencyProfile
        # Exclude the actual 'user' field as we are taking 'user_id' input
        # List fields expected in the POST body (besides user_id and images)
        fields = [
            'user_id', 'agency_name', 'contact1', 'contact2', 'agency_type',
            'website', 'date_of_establishment', 'volunteers', 'address',
            'district', 'state', 'lat', 'lng', 'description'
        ]

    def validate_user_id(self, value):
        """Check if user_id is valid and doesn't have a profile yet."""
        try:
            user = User.objects.get(pk=value, role='agency')
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist or is not an agency.")

        if AgencyProfile.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Agency profile already exists for this user.")
        return value

# --- Serializer for UPDATING Agency Profile (No Auth) ---
class AgencyProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for UPDATING AgencyProfile fields.
    """
    class Meta:
        model = AgencyProfile
        # Fields allowed for update via PUT/PATCH
        # Exclude the primary key ('user') and timestamps
        exclude = ['user', 'created_at', 'updated_at']

# --- Serializer for LISTING Agency Profiles (No Auth, No Images) ---
class AgencyProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for LISTING AgencyProfiles concisely (no images/description).
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True) # Use source='user.id'

    class Meta:
        model = AgencyProfile
        # Concise list of fields for display
        fields = [
            'user_id', 'email', 'agency_name', 'contact1', 'district', 'state',
            'lat', 'lng', 'agency_type'
        ]
        read_only_fields = fields

# --- Serializer for RETRIEVING Agency Profile (No Auth, With Images) ---
class AgencyProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for RETRIEVING a single AgencyProfile with details and images.
    """
    images = AgencyImageSerializer(many=True, read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True) # Use source='user.id'

    class Meta:
        model = AgencyProfile
        # All relevant fields including nested images
        fields = [
            'user_id', 'email', 'agency_name', 'contact1', 'contact2', 'agency_type',
            'website', 'date_of_establishment', 'volunteers', 'address',
            'district', 'state', 'lat', 'lng', 'description',
            'created_at', 'updated_at', 'images'
        ]
        read_only_fields = fields # Primarily for display


class VolunteerInterestSubmitSerializer(serializers.Serializer): # Inherit from base Serializer
    """
    Serializer for creating VolunteerInterest records without authentication.
    Expects volunteer_id and agency_id directly in the request data.
    Handles fetching related user/agency objects during creation.
    """
    # Define the fields expected directly from the frontend request body
    volunteer_id = serializers.IntegerField(
        write_only=True, # Only used for input, not output
        required=True,
        help_text="The ID of the user submitting the interest."
    )
    agency_id = serializers.IntegerField(
        write_only=True, # Only used for input, not output
        required=True,
        help_text="The ID of the agency receiving the interest."
    )
    message = serializers.CharField(
        required=False, # Optional field
        allow_blank=True,
        allow_null=True,
        style={'base_template': 'textarea.html'},
        help_text="Optional message from the volunteer."
    )

    # We are not using ModelSerializer's automatic features here,
    # so we define the create method explicitly.

    def create(self, validated_data):
        """
        Handles creation of the VolunteerInterest object from IDs.
        """
        volunteer_id = validated_data['volunteer_id']
        agency_id = validated_data['agency_id']
        message = validated_data.get('message') # Use .get() for optional field

        try:
            # Fetch the actual User object for the volunteer using the provided ID
            # Add role='user' check for safety, even without auth
            volunteer_user = User.objects.get(id=volunteer_id, role='user')
        except User.DoesNotExist:
            # If the user doesn't exist or isn't a 'user', raise a validation error
            raise serializers.ValidationError(
                {'volunteer_id': f'No active user found with ID {volunteer_id} and role "user".'}
            )

        try:
            # Fetch the actual User object for the agency using the provided ID
            # Add role='agency' check for safety
            agency_user = User.objects.get(id=agency_id, role='agency')
        except User.DoesNotExist:
            # If the agency doesn't exist or isn't an 'agency', raise a validation error
            raise serializers.ValidationError(
                {'agency_id': f'No active agency found with ID {agency_id} and role "agency".'}
            )

        # --- Optional: Check for duplicate submissions ---
        # Decide if you want to prevent multiple interests from the same volunteer to the same agency.
        # If using unique_together in model, this check provides a cleaner error.
        # If allowing duplicates, comment out this block.
        if VolunteerInterest.objects.filter(volunteer=volunteer_user, agency=agency_user).exists():
             raise serializers.ValidationError(
                 "Volunteer interest has already been submitted by this user for this agency."
             )
        # --- End of Optional Duplicate Check ---

        # Create the VolunteerInterest instance using the fetched objects
        try:
            interest = VolunteerInterest.objects.create(
                volunteer=volunteer_user,
                agency=agency_user,
                message=message
                # submitted_at is handled by auto_now_add=True in the model
            )
            return interest
        except Exception as e:
            # Catch potential database errors during creation
            raise serializers.ValidationError(f"Failed to create volunteer interest record: {e}")

    # No need for an 'update' method if this serializer is only for creation.
 

class VolunteerInterestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for UPDATING the is_accepted status
    of a VolunteerInterest record by an agency.
    """
    # is_accepted = serializers.BooleanField(required=True) # Explicit is okay, but often not needed

    class Meta:
        model = VolunteerInterest
        # Only include the field(s) that should be updatable via this serializer
        fields = ['is_accepted']
        # IMPORTANT: Do not list 'is_accepted' in read_only_fields here!
# ---serializer for showing the all the volunteer list 

# class VolunteerInterestListSerializer(serializers.ModelSerializer):
#     """
#     Serializer for listing VolunteerInterest records.
#     This serializer is used to display the list of interests.
#     """
#     class Meta:
#         model = VolunteerInterest
#         fields = [
#             'id', 'volunteer', 'agency', 'message', 'is_accepted', 
#             'submitted_at'
#         ]
#         read_only_fields = ['id', 'submitted_at']
#         # No need to include 'is_accepted' in read_only_fields


class VolunteerInterestListSerializer(serializers.ModelSerializer):
    # """
    # Serializer for DISPLAYING VolunteerInterest records.
    # Includes specific details (email, name, contact) from the related volunteer user.
    # """
    # --- Add fields pulling data from the related volunteer ---
    volunteer_email = serializers.EmailField(source='volunteer.email', read_only=True)
    volunteer_name = serializers.CharField(source='volunteer.full_name', read_only=True)
    volunteer_contact = serializers.CharField(source='volunteer.contact', read_only=True)
    # --- End added fields ---

    # Optionally, you can still include the agency ID or nested agency info
    # agency_name = serializers.CharField(source='agency.agency_profile.agency_name', read_only=True) # Example

    class Meta:
        model = VolunteerInterest
        fields = [
            'id',
            'volunteer', # This will still show the volunteer's ID
            # --- Include the new fields ---
            'volunteer_email',
            'volunteer_name',
            'volunteer_contact',
            # --- End new fields ---
            'agency', # Shows agency ID
            'message',
            'submitted_at',
            'is_accepted'
        ]
        # Mark all as read-only for safety in a list view
        read_only_fields = fields        



class ExistingAgenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExistingAgencies
        fields = '__all__'  # This will include all fields in the model

class EventSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)  # Accept user_id in the request

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'date', 'start_time', 'event_type', 'platform', 'meeting_link', 
            'meeting_id', 'venue_name', 'address', 'district', 'state', 'attendees', 
            'reg_type', 'tags', 'description', 'location_type', 'timeline_items', 'user_id'
        ]

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')  # Get the user_id from the request data
        user = User.objects.get(id=user_id)  # Get the user from the user_id
        event = Event.objects.create(user_id=user, **validated_data)  # Create the event and link to the user
        
        return event

    def update(self, instance, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id:
            user = User.objects.get(id=user_id)
            instance.user_id = user

        # Update other fields
        instance.name = validated_data.get('name', instance.name)
        instance.date = validated_data.get('date', instance.date)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.event_type = validated_data.get('event_type', instance.event_type)
        instance.platform = validated_data.get('platform', instance.platform)
        instance.meeting_link = validated_data.get('meeting_link', instance.meeting_link)
        instance.meeting_id = validated_data.get('meeting_id', instance.meeting_id)
        instance.venue_name = validated_data.get('venue_name', instance.venue_name)
        instance.address = validated_data.get('address', instance.address)
        instance.district = validated_data.get('district', instance.district)
        instance.state = validated_data.get('state', instance.state)
        instance.attendees = validated_data.get('attendees', instance.attendees)
        instance.reg_type = validated_data.get('reg_type', instance.reg_type)
        instance.tags = validated_data.get('tags', instance.tags)
        instance.description = validated_data.get('description', instance.description)
        instance.location_type = validated_data.get('location_type', instance.location_type)
        instance.timeline_items = validated_data.get('timeline_items', instance.timeline_items)

        instance.save()
        return instance
    
    

class BasicUserSerializer(serializers.ModelSerializer):
    """
    Serializer for basic user information (read-only).
    """
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email'] # Adjust fields as needed
        read_only_fields = fields

class BasicEventSerializer(serializers.ModelSerializer):
    """
    Serializer for basic event information (read-only).
    """
    class Meta:
        model = Event
        fields = ['id', 'name', 'date', 'event_type'] # Adjust fields as needed
        read_only_fields = fields
        
# agency/serializers.py (continued)

class EventInterestSerializer(serializers.ModelSerializer):
    # For readable responses, use the basic serializers
    user = BasicUserSerializer(read_only=True)
    event = BasicEventSerializer(read_only=True)

    # For input when creating/updating, accept IDs
    user_id_input = serializers.IntegerField(write_only=True, source='user_id_val') # Use a different source name
    event_id_input = serializers.IntegerField(write_only=True, source='event_id_val') # Use a different source name

    class Meta:
        model = EventInterest
        fields = [
            'id',
            'user',             # Read-only nested object for GET
            'event',            # Read-only nested object for GET
            'user_id_input',    # Write-only field for POST/PUT user ID
            'event_id_input',   # Write-only field for POST/PUT event ID
            'interested',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at'] # user and event are handled by their serializers

    def create(self, validated_data):
        user_id = validated_data.pop('user_id_val')
        event_id = validated_data.pop('event_id_val')
        interested_status = validated_data.get('interested', True) # Default to True if creating

        try:
            user_instance = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id_input": f"User with id {user_id} does not exist."})

        try:
            event_instance = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event_id_input": f"Event with id {event_id} does not exist."})

        # Use update_or_create to handle both new interests and updates to existing ones
        interest_obj, created = EventInterest.objects.update_or_create(
            user=user_instance,
            event=event_instance,
            defaults={'interested': interested_status}
        )
        if created and interested_status and user_instance.email:
            from django.core.mail import send_mail
            subject = f"Registration Confirmed: {event_instance.name}"
            message = (
                f"Dear {user_instance.full_name or user_instance.email},\n\n"
                f"You have successfully registered for the event: {event_instance.name}.\n"
                f"Date: {event_instance.date}\n"
                f"Time: {event_instance.start_time}\n"
                f"Venue: {event_instance.venue_name or event_instance.platform or 'TBA'}\n\n"
                f"Thank you for your interest!\n"
                f"Best regards,\n"
                f"Disaster Sentinel Team"
            )
            send_mail(
                subject,
                message,
                None,  # Use default from settings
                [user_instance.email],
                fail_silently=True,
            )
        return interest_obj

    def update(self, instance, validated_data):
        # user_id and event_id are not typically changed on update for an existing interest record.
        # The primary key of EventInterest (instance.id) identifies the record.
        # We only update the 'interested' status.
        instance.interested = validated_data.get('interested', instance.interested)
        instance.save()
        return instance
    
    