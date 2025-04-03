from django.db import models

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import cloudinary
import cloudinary.uploader
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

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

# class ExistingAgencies(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=255)
#     address = models.CharField(max_length=255)
#     state = models.CharField(max_length=255)
#     district = models.CharField(max_length=255)
#     email = models.EmailField()
#     telephone = models.CharField(max_length=15)
#     phone = models.CharField(max_length=15)
#     category = models.CharField(max_length=255)
    
#     class Meta:
#         db_table = 'agency_details'
#         managed = False
    
#     def __str__(self):
#         return self.name
    

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