# agency/admin.py

from django.contrib import admin
# Use settings to get the custom user model configured in your project
from django.conf import settings
# Import models from the current app (.)
from .models import (
    ExistingAgencies,
    MissingPersonReport,
    AgencyProfile,
    AgencyImage,
    VolunteerInterest
)
# Import utility for displaying images if needed (optional, requires extra setup sometimes)
# from django.utils.html import format_html

# Get the Custom User model defined in settings.AUTH_USER_MODEL
# Useful if searching/filtering based on user fields not directly on the profile
User = settings.AUTH_USER_MODEL

# --- Inline Admin for Agency Images ---
class AgencyImageInline(admin.TabularInline):
    """
    Allows managing AgencyImage records directly within the AgencyProfile admin page.
    TabularInline shows them in a table format.
    """
    model = AgencyImage
    fields = ('image', 'caption', 'uploaded_at') # Fields to display/edit in the inline form
    readonly_fields = ('uploaded_at',) # Make timestamp read-only
    extra = 1 # Show 1 extra blank form for adding a new image by default
    # Optional: Add preview for Cloudinary image if default isn't sufficient
    # def image_preview(self, obj):
    #     if obj.image:
    #         return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
    #     return "(No image)"
    # readonly_fields = ('uploaded_at', 'image_preview')
    # fields = ('image_preview', 'image', 'caption', 'uploaded_at')


# --- Admin Configuration for AgencyProfile ---
@admin.register(AgencyProfile)
class AgencyProfileAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for AgencyProfile model.
    Includes inline editing for AgencyImages.
    """
    # Display these fields in the main list view
    list_display = ('user', 'agency_name', 'state', 'district', 'updated_at')
    # Enable searching across these fields (use __ for related fields)
    search_fields = ('user__email', 'user__full_name', 'agency_name', 'state', 'district', 'address')
    # Add filters to the sidebar
    list_filter = ('state', 'district', 'agency_type', 'updated_at')
    # Make linked user and timestamps read-only in the detail view
    readonly_fields = ('user', 'created_at', 'updated_at')
    # Include the AgencyImageInline defined above
    inlines = [AgencyImageInline]
    # Organize fields in the edit/add form (optional but recommended)
    fieldsets = (
        ('User Link', {'fields': ('user',)}),
        ('Agency Details', {'fields': ('agency_name', 'agency_type', 'date_of_establishment', 'website')}),
        ('Contact Info', {'fields': ('contact1', 'contact2')}),
        ('Location', {'fields': ('address', 'district', 'state', 'lat', 'lng')}),
        ('Description & Stats', {'fields': ('description', 'volunteers')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# --- Admin Configuration for VolunteerInterest ---
@admin.register(VolunteerInterest)
class VolunteerInterestAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for VolunteerInterest model.
    Allows easy viewing, filtering, and acceptance of requests.
    """
    # Fields to display in the list view
    list_display = ('volunteer_email', 'agency_email', 'submitted_at', 'is_accepted')
    # Allow editing 'is_accepted' directly in the list view!
    list_editable = ('is_accepted',)
    # Add filters
    list_filter = ('is_accepted', 'agency__agency_profile__state', 'submitted_at') # Filter by agency's state
    # Enable searching
    search_fields = ('volunteer__email', 'agency__email', 'message', 'agency__agency_profile__agency_name') # Search by related fields
    # Make fields read-only in the detail form (acceptance done via list_editable)
    readonly_fields = ('volunteer', 'agency', 'message', 'submitted_at')
    # Control fields shown in the detail view form
    fields = ('volunteer', 'agency', 'message', 'submitted_at', 'is_accepted')

    # Custom methods to display related user emails in list_display
    @admin.display(description='Volunteer Email', ordering='volunteer__email')
    def volunteer_email(self, obj):
        return obj.volunteer.email

    @admin.display(description='Agency Email', ordering='agency__email')
    def agency_email(self, obj):
        return obj.agency.email


# --- Existing Registrations (Keep these) ---

@admin.register(MissingPersonReport)
class MissingPersonReportAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'reporter', 'last_seen_location', 'created_at')
    search_fields = ('full_name', 'reporter__email', 'identification_marks', 'description')
    list_filter = ('has_id_card', 'has_person_photo', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'last_seen_location', 'identification_marks', 'description')
        }),
        ('Photos', {
            'fields': ('person_photo', 'id_card_photo')
        }),
        ('Metadata', {
            'fields': ('reporter', 'created_at', 'updated_at')
        }),
    )

# Simple registration for ExistingAgencies (if no customization needed)
admin.site.register(ExistingAgencies)

# Note: Ensure your CustomUser model is also registered appropriately,
# usually in the admin.py of your 'users' app. If it's not registered,
# some related field lookups might not work as expected in the admin.
# Example (typically in users/admin.py):
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import CustomUser
# class CustomUserAdmin(BaseUserAdmin):
#     # Add custom fields to display/edit
#     pass
# admin.site.register(CustomUser, CustomUserAdmin)

