from django.contrib import admin

# Register your models here.

from .models import ExistingAgencies
from .models import MissingPersonReport

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

admin.site.register(ExistingAgencies)

