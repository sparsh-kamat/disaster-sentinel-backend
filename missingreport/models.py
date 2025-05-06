# missingreport/models.py

from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _

# Get your CustomUser model
User = settings.AUTH_USER_MODEL

class MissingPersonReport(models.Model):
    """
    Stores details about a missing person report submitted by a user.
    Includes new fields for age, gender, location, and disaster context.
    """
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    DISASTER_TYPE_CHOICES = [
        ('Cyclones', 'Cyclones'),
        ('Earthquakes', 'Earthquakes'),
        ('Tsunamis', 'Tsunamis'),
        ('Floods', 'Floods'),
        ('Landslides', 'Landslides'),
        ('Fire', 'Fire'),
        ('Heatwave', 'Heatwave'),
        ('Other', 'Other'),
        # Add more types as needed
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_missing_reports',
        help_text=_("The user who submitted this report.")
    )

    # Renamed from 'name' in form to 'full_name' in model
    full_name = models.CharField(max_length=255, help_text=_("Full name of the missing person."))
    age = models.PositiveIntegerField(null=True, blank=True, help_text=_("Age of the missing person (optional)."))
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, help_text=_("Gender of the missing person (optional)."))
    description = models.TextField(help_text=_("Detailed description of the person and circumstances."))
    identification_marks = models.TextField(blank=True, null=True, help_text=_("Distinctive identification marks (optional)."))
    # Renamed from 'lastSeenPlace' in form to 'last_seen_location' in model
    last_seen_location = models.TextField(help_text=_("Text description of where and when the person was last seen (from form's lastSeenPlace)."))
    state = models.CharField(max_length=100, blank=True, null=True, help_text=_("State where the person was last seen or resides."))
    district = models.CharField(max_length=100, blank=True, null=True, help_text=_("District where the person was last seen or resides."))
    # Renamed from 'disasterType' in form
    disaster_type = models.CharField(max_length=50, choices=DISASTER_TYPE_CHOICES, blank=True, null=True, help_text=_("Type of disaster associated with the missing person report (optional)."))
    # Renamed from 'contactInfo' in form
    reporter_contact_info = models.CharField(max_length=255, help_text=_("Contact information provided by the reporter for this case."))
    # Renamed from 'additionalInfo' in form
    additional_info = models.TextField(blank=True, null=True, help_text=_("Any other relevant information (optional)."))

    # Identity Card Image - Optional
    identity_card_image = CloudinaryField(
        'missing_persons/identity_cards',
        blank=True,
        null=True,
        help_text=_("Uploaded photo of the missing person's identity card (optional).")
    )

    # Person Photo - Assuming mandatory based on form
    person_photo = CloudinaryField(
        'missing_persons/photos',
        help_text=_("Uploaded photo of the missing person.")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Missing Person Report")
        verbose_name_plural = _("Missing Person Reports")

    def __str__(self):
        return f"Report for {self.full_name} by {self.reporter.email if self.reporter else 'Deleted User'}"

