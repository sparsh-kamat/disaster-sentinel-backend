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
 # ForeignKey to the CustomUser model (instead of User)
     # Explicitly use user_id to refer to the user who created the event
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', to_field='id', db_column='user_id')  # Link to the user who created the event

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
    
    def __str__(self):
        return self.name

class TimelineItem(models.Model):
    event = models.ForeignKey(Event, related_name="timeline_items", on_delete=models.CASCADE)
    time = models.TimeField()
    activity = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.time} - {self.activity}"

class ExistingAgencies(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    category = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'agency_details'
        managed = False
    
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