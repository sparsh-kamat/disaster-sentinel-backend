from django.contrib import admin
from .models import MissingPersonReport # Import your MissingPersonReport model

@admin.register(MissingPersonReport)
class MissingPersonReportAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'reporter_email', # Custom method to display reporter's email
        'age',
        'gender',
        'last_seen_location_summary', # Custom method for brevity
        'state',
        'district',
        'disaster_type',
        'is_found',
        'found_date',
        'marked_found_by_type',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'is_found',
        'gender',
        'disaster_type',
        'state',
        'district',
        'marked_found_by_type',
        'created_at',
        'found_date',
    )
    search_fields = (
        'full_name',
        'description',
        'identification_marks',
        'last_seen_location',
        'reporter__email', # Search by reporter's email
        'reporter__full_name', # Search by reporter's full name
        'state',
        'district',
    )
    readonly_fields = ('created_at', 'updated_at', 'identity_card_image_display', 'person_photo_display')
    autocomplete_fields = ['reporter', 'marked_found_by_user'] # Makes ForeignKey fields searchable

    fieldsets = (
        (None, {
            'fields': ('reporter', 'full_name', 'age', 'gender', 'description', 'identification_marks')
        }),
        ('Last Seen Information', {
            'fields': ('last_seen_location', 'state', 'district', 'disaster_type')
        }),
        ('Contact & Additional Information', {
            'fields': ('reporter_contact_info', 'additional_info')
        }),
        ('Images', {
            # Display current images if they exist, and allow new uploads.
            # For CloudinaryField, direct display might need custom widget or readonly_fields with display methods.
            'fields': ('person_photo', 'person_photo_display', 'identity_card_image', 'identity_card_image_display')
        }),
        ('Found Status (Editable by Admin)', {
            'classes': ('collapse',), # Collapsible section
            'fields': (
                'is_found',
                'found_date',
                'marked_found_by_type',
                'marked_found_by_user', # This will be a dropdown for admin to select
                'agency_found_location',
                'agency_current_location_of_person',
                'agency_person_condition',
                'agency_found_notes',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def reporter_email(self, obj):
        if obj.reporter:
            return obj.reporter.email
        return None
    reporter_email.short_description = 'Reporter Email'

    def last_seen_location_summary(self, obj):
        if obj.last_seen_location:
            return (obj.last_seen_location[:75] + '...') if len(obj.last_seen_location) > 75 else obj.last_seen_location
        return None
    last_seen_location_summary.short_description = 'Last Seen At'

    def identity_card_image_display(self, obj):
        from django.utils.html import format_html
        if obj.identity_card_image and hasattr(obj.identity_card_image, 'url'):
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="150" /></a>', obj.identity_card_image.url)
        return "(No ID Card Image)"
    identity_card_image_display.short_description = 'ID Card Preview'

    def person_photo_display(self, obj):
        from django.utils.html import format_html
        if obj.person_photo and hasattr(obj.person_photo, 'url'):
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="150" /></a>', obj.person_photo.url)
        return "(No Person Photo)"
    person_photo_display.short_description = 'Person Photo Preview'

    def get_queryset(self, request):
        # Optimize query by prefetching related reporter details
        return super().get_queryset(request).select_related('reporter', 'marked_found_by_user')

