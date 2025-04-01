from django.db import models

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator



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
    
    # Photo fields
    person_photo = models.ImageField(
        upload_to='missing_persons/photos/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    id_card_photo = models.ImageField(
        upload_to='missing_persons/id_cards/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    
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