from django.db import models
from django.utils.translation import gettext_lazy as _

class GdacsDisasterEvent(models.Model):
    """
    Stores information about disaster events fetched from GDACS, focusing on India.
    Includes the state determined by reverse geocoding.
    """
    eventid = models.CharField(
        max_length=50,
        unique=True,
        primary_key=True,
        help_text=_("Unique GDACS Event ID (used as PK)")
    )
    title = models.CharField(max_length=255, help_text=_("Title of the event from the feed."))
    description = models.TextField(blank=True, null=True, help_text=_("Description of the event."))
    link = models.URLField(max_length=512, help_text=_("Link to the GDACS event page."))
    pubDate = models.DateTimeField(null=True, blank=True, help_text=_("Publication date from the feed."))
    latitude = models.FloatField(null=True, blank=True, help_text=_("Latitude coordinate."))
    longitude = models.FloatField(null=True, blank=True, help_text=_("Longitude coordinate."))

    # --- NEW/UPDATED FIELD ---
    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True, # Index for faster filtering by state
        help_text=_("State/Province determined via reverse geocoding (if available).")
    )
    # --- END NEW/UPDATED FIELD ---

    eventtype = models.CharField(max_length=50, db_index=True, help_text=_("Type of event (e.g., EQ, TC, FL)."))
    alertlevel = models.CharField(max_length=20, blank=True, null=True, db_index=True, help_text=_("Alert level (Green, Orange, Red)."))
    severity = models.CharField(max_length=100, blank=True, null=True, help_text=_("Severity description (e.g., 'M 7.1')."))
    population = models.CharField(max_length=50, blank=True, null=True, help_text=_("Affected population estimate (textual)."))
    country = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text=_("Country name(s)."))
    iso3 = models.CharField(max_length=10, blank=True, null=True, db_index=True, help_text=_("ISO3 country code."))
    fromdate = models.DateTimeField(null=True, blank=True, help_text=_("Start date/time of the event."))
    todate = models.DateTimeField(null=True, blank=True, help_text=_("End date/time of the event."))
    iscurrent = models.BooleanField(default=True, db_index=True, help_text=_("Flag indicating if the event is currently listed as active by GDACS."))

    # Timestamps managed by Django
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pubDate', '-fromdate'] # Order by most recent dates first
        verbose_name = "GDACS Disaster Event"
        verbose_name_plural = "GDACS Disaster Events"

    def __str__(self):
        state_info = f" ({self.state})" if self.state else ""
        return f"{self.eventtype} - {self.title}{state_info} ({self.eventid})"



class PastDisaster(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=7)
    longitude = models.DecimalField(max_digits=9, decimal_places=7)
    title = models.CharField(max_length=255)
    year = models.IntegerField()
    month = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    state = models.CharField(max_length=100)
    disaster_type = models.CharField(max_length=100)
    total_deaths = models.IntegerField()
    total_injured = models.IntegerField()
    total_affected = models.BigIntegerField()
    loss_inr = models.BigIntegerField()
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'past_disasters'  # Use the same table name in the database
        # not managed by django
        managed = False

    def __str__(self):
        return f'{self.title} ({self.year})'
