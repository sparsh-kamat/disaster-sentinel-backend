# missingreport/serializers.py

from rest_framework import serializers
# Adjust model imports as needed
from .models import MissingPersonReport
from users.models import CustomUser # Assuming user model is in 'users' app

# --- Serializer for Nested Reporter Details ---
class ReporterInfoSerializer(serializers.ModelSerializer):
    """Read-only serializer for basic reporter info."""
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'contact'] # Fields to display about reporter
        read_only = True

# --- Serializer for Creating Reports (No Auth) ---
class MissingPersonReportCreateSerializer(serializers.ModelSerializer):
    """Handles creation, expects reporter_id. Files handled via request.FILES."""
    reporter_id = serializers.IntegerField(
        write_only=True,
        required=True,
        help_text="ID of the user submitting the report."
    )
    # identity_card_image and person_photo are handled via request.FILES
    # They are not explicitly listed here for input validation via serializer fields

    class Meta:
        model = MissingPersonReport
        # Fields expected from the form data (excluding files and reporter itself)
        fields = [
            'reporter_id', 'full_name', 'description', 'identification_marks',
            'last_seen_location', 'reporter_contact_info'
        ]

    def validate_reporter_id(self, value):
        """Check if reporter_id is valid."""
        if not CustomUser.objects.filter(pk=value).exists():
            raise serializers.ValidationError("User with the provided reporter_id does not exist.")
        return value

# --- Serializer for Listing Reports (Concise) ---
class MissingPersonReportListSerializer(serializers.ModelSerializer):
    """Concise representation for listing reports."""
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True, allow_null=True)
    # Indicate if images exist without sending full URLs
    has_identity_card = serializers.SerializerMethodField(read_only=True)
    has_person_photo = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MissingPersonReport
        fields = [
            'id', 'full_name', 'reporter_email', 'last_seen_location',
            'created_at', 'has_identity_card', 'has_person_photo'
        ]
        read_only_fields = fields

    def get_has_identity_card(self, obj):
        # Check if the identity_card_image field has a value (CloudinaryField stores URL or None)
        return bool(obj.identity_card_image)

    def get_has_person_photo(self, obj):
        # Check if the person_photo field has a value
        return bool(obj.person_photo)

# --- Serializer for Report Details (With Image URLs & Reporter) ---
class MissingPersonReportDetailSerializer(serializers.ModelSerializer):
    """Detailed representation including image URLs and nested reporter info."""
    reporter = ReporterInfoSerializer(read_only=True) # Use nested serializer for reporter

    class Meta:
        model = MissingPersonReport
        # Include all model fields and nested reporter
        fields = [
            'id',
            'reporter', # Nested reporter details
            'full_name', 'description', 'identification_marks',
            'last_seen_location', 'reporter_contact_info',
            'identity_card_image', # Will contain URL or null
            'person_photo',        # Will contain URL or null
            'created_at', 'updated_at',
        ]
        read_only_fields = fields # Primarily for display
