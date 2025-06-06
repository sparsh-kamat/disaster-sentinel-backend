# missingreport/serializers.py

from rest_framework import serializers
from .models import MissingPersonReport
from users.models import CustomUser # Assuming user model is in 'users' app

# --- Serializer for Nested Reporter Details (No change needed) ---
class ReporterInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'contact']
        read_only = True

# --- Serializer for Creating Reports (No Auth) ---
class MissingPersonReportCreateSerializer(serializers.ModelSerializer):
    reporter_id = serializers.IntegerField(write_only=True, required=True)
    # Frontend sends 'name', 'age', 'gender', 'description', 'identificationMarks',
    # 'lastSeenPlace', 'state', 'district', 'disasterType', 'contactInfo', 'additionalInfo'
    # We need to map these to model fields if names differ.

    # Explicitly define fields from frontend if names differ or need specific validation
    name = serializers.CharField(source='full_name', max_length=255, write_only=True, required=True)
    age = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    gender = serializers.ChoiceField(choices=MissingPersonReport.GENDER_CHOICES, required=False, allow_null=True, write_only=True)
    # description is same
    identificationMarks = serializers.CharField(source='identification_marks', required=False, allow_blank=True, allow_null=True, write_only=True)
    lastSeenPlace = serializers.CharField(source='last_seen_location', write_only=True, required=True)
    # state is same
    # district is same
    disasterType = serializers.ChoiceField(source='disaster_type', choices=MissingPersonReport.DISASTER_TYPE_CHOICES, required=False, allow_null=True, write_only=True)
    contactInfo = serializers.CharField(source='reporter_contact_info', max_length=255, write_only=True, required=True)
    additionalInfo = serializers.CharField(source='additional_info', required=False, allow_blank=True, allow_null=True, write_only=True)


    class Meta:
        model = MissingPersonReport
        # List all fields that the serializer will handle for creation.
        # These are the fields that will be in validated_data after is_valid()
        # and before being passed to model instance creation.
        fields = [
            'reporter_id',
            'name', # from frontend, maps to full_name
            'age',
            'gender',
            'description',
            'identificationMarks', # from frontend, maps to identification_marks
            'lastSeenPlace', # from frontend, maps to last_seen_location
            'state',
            'district',
            'disasterType', # from frontend, maps to disaster_type
            'contactInfo', # from frontend, maps to reporter_contact_info
            'additionalInfo', # from frontend, maps to additional_info
            # File fields (identity_card_image, person_photo) are handled directly from request.FILES in the view
        ]

    def validate_reporter_id(self, value):
        if not CustomUser.objects.filter(pk=value).exists():
            raise serializers.ValidationError("User with the provided reporter_id does not exist.")
        return value
    
# --- Serializer for User to Update Additional Info ---
class MissingPersonReportUpdateInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissingPersonReport
        fields = ['additional_info'] # Only this field can be updated
   
   
# --- Serializer for Agency to Mark Person as Found ---
class AgencyMarkFoundSerializer(serializers.ModelSerializer):
    # We expect agency to provide these details
    agency_found_location = serializers.CharField(required=True)
    agency_current_location_of_person = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    agency_person_condition = serializers.ChoiceField(choices=MissingPersonReport.CONDITION_CHOICES, required=True)
    found_date = serializers.DateField(required=True) # Agency provides this
    agency_found_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = MissingPersonReport
        fields = [
            'agency_found_location',
            'agency_current_location_of_person',
            'agency_person_condition',
            'found_date',
            'agency_found_notes',
            # is_found will be set to True in the view
        ]


   

# --- Serializer for Listing Reports (Concise) ---
class MissingPersonReportListSerializer(serializers.ModelSerializer):
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True, allow_null=True)
    has_identity_card = serializers.SerializerMethodField(read_only=True)
    has_person_photo = serializers.SerializerMethodField(read_only=True)
    # Add is_found status
    is_found = serializers.BooleanField(read_only=True)

    class Meta:
        model = MissingPersonReport
        fields = [
            'id', 'full_name', 'age', 'gender', # Added age, gender
            'reporter_email', 'last_seen_location', 'state', 'district', # Added state, district
            'disaster_type', # Added disaster_type
            'created_at', 'has_identity_card', 'has_person_photo', 'is_found',
        ]
        read_only_fields = fields

    def get_has_identity_card(self, obj):
        return bool(obj.identity_card_image)

    def get_has_person_photo(self, obj):
        return bool(obj.person_photo)

# --- Serializer for Report Details (With Image URLs & Reporter) ---
class MissingPersonReportDetailSerializer(serializers.ModelSerializer):
    reporter = ReporterInfoSerializer(read_only=True)
    marked_found_by_user_email = serializers.EmailField(source='marked_found_by_user.email', read_only=True, allow_null=True)


    class Meta:
        model = MissingPersonReport
        fields = [
            'id', 'reporter', 'full_name', 'age', 'gender', 'description',
            'identification_marks', 'last_seen_location', 'state', 'district',
            'disaster_type', 'reporter_contact_info', 'additional_info',
            'identity_card_image', 'person_photo',
            'created_at', 'updated_at',
            # "Found" details
            'is_found', 'found_date', 'marked_found_by_type',
            'marked_found_by_user_email', # Show email of user who marked found
            'agency_found_location', 'agency_current_location_of_person',
            'agency_person_condition', 'agency_found_notes'
        ]
        read_only_fields = fields
