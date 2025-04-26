#missingreport/models.py

from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils.translation import gettext_lazy as _

# Get your CustomUser model
User = settings.AUTH_USER_MODEL

class MissingPersonReport(models.Model):
    """
    Stores details about a missing person report submitted by a user.
    Includes fields for one ID card photo and one person photo.
    """
    # Link to the user who submitted the report
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # Keep report even if reporter account is deleted
        null=True, # Allow null if reporter is deleted
        related_name='submitted_missing_reports',
        help_text=_("The user who submitted this report.")
    )

    # Fields from the form
    full_name = models.CharField(max_length=255, help_text=_("Full name of the missing person."))
    description = models.TextField(help_text=_("Detailed description of the person and circumstances."))
    identification_marks = models.TextField(blank=True, null=True, help_text=_("Distinctive identification marks (optional)."))
    last_seen_location = models.TextField(help_text=_("Where and when the person was last seen."))
    reporter_contact_info = models.CharField(max_length=255, help_text=_("Contact information provided by the reporter for this case."))

    # Identity Card Image (using Cloudinary) - Optional
    identity_card_image = CloudinaryField(
        'missing_persons/identity_cards', # Folder in Cloudinary
        blank=True, # Optional field
        null=True,
        help_text=_("Uploaded photo of the missing person's identity card (optional).")
    )

    # Person Photo field - Assuming mandatory
    person_photo = CloudinaryField(
        'missing_persons/photos', # Folder in Cloudinary
        # Remove blank=True, null=True if this photo is mandatory
        help_text=_("Uploaded photo of the missing person.")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Missing Person Report")
        verbose_name_plural = _("Missing Person Reports")

    def __str__(self):
        return f"Report for {self.full_name} by {self.reporter.email if self.reporter else 'Deleted User'}"

