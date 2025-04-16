from django.db import models

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import cloudinary
import cloudinary.uploader
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
class VolunteerInterest(models.Model):
    """
    Represents a user's submitted interest in volunteering for an Agency.
    (Simplified version - captures submission details only).
    """
    # Link to the user expressing interest
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Or models.SET_NULL if you want to keep the record even if user is deleted
        related_name='volunteer_interests_submitted', # user.volunteer_interests_submitted.all()
        limit_choices_to={'role': 'user'},
        help_text=("The user expressing interest in volunteering.")
    )

    # Link to the agency the user is interested in
    agency = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Or models.SET_NULL
        related_name='received_volunteer_interests', # agency.received_volunteer_interests.all()
        limit_choices_to={'role': 'agency'},
        help_text=("The agency the user is interested in volunteering for.")
    )

    # Optional message from the volunteer
    message = models.TextField(
        blank=True, # Field is not required
        null=True,  # Database column can be NULL
        help_text=("Optional message submitted by the volunteer.")
    )

    # Timestamp for when the interest was submitted
    submitted_at = models.DateTimeField(
        auto_now_add=True, # Automatically set when the record is created
        help_text=("Timestamp indicating when the interest was submitted.")
    )
    
    # --- NEW FIELD to track acceptance ---
    is_accepted = models.BooleanField(
        default=False, # Interest is not accepted by default when submitted
        db_index=True, # Add index if you plan to filter by accepted status often
        help_text=("Set to True if the agency accepts this volunteer interest.")
    )

    class Meta:
        verbose_name = ("Volunteer Interest")
        verbose_name_plural = ("Volunteer Interests")
        ordering = ['-submitted_at'] # Show the most recent submissions first

        # --- Optional Constraint ---
        # Do you want to prevent a user from submitting interest to the same agency multiple times?
        # If yes, uncomment the line below. This means a user can only appear once per agency in this table.
        # unique_together = ('volunteer', 'agency')
        # If you allow multiple submissions, leave it commented out.

    def __str__(self):
        # Readable representation of the object
        return f"Interest from {self.volunteer.email} for {self.agency.email} at {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"


class AgencyMemberPermission(models.Model):
    """
    Defines specific permissions granted by an Agency user
    to another User (member) within the context of that agency.
    """
    agency = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='granted_permissions', # Allows agency_user.granted_permissions.all()
        limit_choices_to={'role': 'agency'}, # IMPORTANT: Ensures this FK only points to agency-role users
        help_text="The agency granting the permissions."
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agency_permissions', # Allows member_user.agency_permissions.filter(agency=...)
        # Optional: Limit choices if only 'user' role can be members
        # limit_choices_to={'role': 'user'},
        help_text="The user receiving the permissions."
    )

    # --- Specific Boolean Permissions ---
    # Based on your previous suggestion:
    can_view_missing = models.BooleanField(default=False, verbose_name="Can View Missing Person Reports")
    can_edit_missing = models.BooleanField(default=False, verbose_name="Can Edit Missing Person Reports")
    can_view_announcements = models.BooleanField(default=False, verbose_name="Can View Agency Announcements")
    can_edit_announcements = models.BooleanField(default=False, verbose_name="Can Edit Agency Announcements")
    can_make_announcements = models.BooleanField(default=False, verbose_name="Can Create New Agency Announcements")
    can_manage_volunteers = models.BooleanField(default=False, verbose_name="Can Manage Agency Volunteers")
    is_agency_admin = models.BooleanField(default=False, verbose_name="Is Agency Admin")
    
    
    # --- Add other permissions as needed for your project ---
    # Example: can_manage_agency_events = models.BooleanField(default=False, verbose_name="Can Manage Agency Events")
    # Example: can_respond_to_alerts = models.BooleanField(default=False, verbose_name="Can Respond to Disaster Alerts")
    # Example: can_manage_volunteers = models.BooleanField(default=False, verbose_name="Can Manage Agency Volunteers")

    # Optional: Timestamps
    granted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures that a specific member can only have one permission entry per agency.
        unique_together = ('agency', 'member')
        verbose_name = "Agency Member Permission"
        verbose_name_plural = "Agency Member Permissions"
        ordering = ['agency', 'member'] # Optional: Default ordering

    def __str__(self):
        # Provides a readable representation in the Django admin or shell
        return f"Permissions for {self.member.email} from Agency {self.agency.email}"



class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ("Conference", "Conference"),
        ("Workshop", "Workshop"),
        ("Seminar", "Seminar"),
        ("Webinar", "Webinar"),
        ("Networking", "Networking"),
        ("Other", "Other"),
    ]

    REG_TYPE_CHOICES = [
        ("Free", "Free"),
        ("Paid", "Paid"),
    ]

    # ForeignKey to the User model (user_id in the event)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', to_field='id', db_column='user_id')

    name = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    platform = models.CharField(max_length=100, null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    meeting_id = models.CharField(max_length=100, null=True, blank=True)
    venue_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    attendees = models.IntegerField(null=True, blank=True)
    reg_type = models.CharField(max_length=50, choices=REG_TYPE_CHOICES)
    description = models.TextField(null=True, blank=True)
    tags = models.JSONField(default=list)
    location_type = models.CharField(max_length=10, choices=[("online", "Online"), ("offline", "Offline")], default="online")

    # Store the timeline items as a JSON field
    timeline_items = models.JSONField(default=list, blank=True)  # Default empty list if no timeline items are provided
    
    def __str__(self):
        return self.name

class ExistingAgencies(models.Model):
    id = models.AutoField(primary_key=True)  # Keep the primary key
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    telephone = models.CharField(max_length=15)
    mobile_no = models.BigIntegerField()  # Updated to match mobile_no in new table
    website = models.URLField(null=True, blank=True)  # Added website field
    registration_date = models.DateField(null=True, blank=True)  # Updated to store as a Date type
    
    class Meta:
        db_table = 'existing_agencies'  # Update to match the correct table name
        managed = False  # Prevent Django from managing this table (as it already exists in DB)

    def __str__(self):
        return self.name
    
class MissingPersonReport(models.Model):
    # Reporter information
    reporter = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE,
        related_name='missing_reports'
    )
    
    # Person details
    full_name = models.CharField(max_length=255)
    last_seen_location = models.CharField(max_length=500)
    identification_marks = models.TextField()
    description = models.TextField(help_text="Detailed description of the missing person")
    
    # Use CloudinaryField instead of ImageField
    person_photo = CloudinaryField('photo', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    id_card_photo = CloudinaryField('id_card', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])

    
    # Status flags
    has_id_card = models.BooleanField(default=False)
    has_person_photo = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Automatically set status flags before saving"""
        self.has_id_card = bool(self.id_card_photo)
        self.has_person_photo = bool(self.person_photo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Missing: {self.full_name} (Reported by: {self.reporter.email})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Missing Person Report'
        verbose_name_plural = 'Missing Person Reports'