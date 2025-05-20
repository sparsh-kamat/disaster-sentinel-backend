# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, OTPStorage # Assuming OTPStorage is also in users.models

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # The forms to use for adding and changing user instances
    # add_form = YourCustomUserCreationForm  # If you have a custom creation form
    # form = YourCustomUserChangeForm      # If you have a custom change form

    list_display = (
        'email',
        'full_name',
        'role',
        'state',
        'district',
        'is_verified',
        'is_staff',
        'is_active',
        'date_joined',
        'last_login'
    )
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active', 'state')
    search_fields = ('email', 'full_name', 'contact', 'agency_pan', 'state', 'district')
    ordering = ('email',)

    # Fieldsets for the change/edit page
    # Note: 'username' is removed as it's None in your CustomUser model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'contact', 'role', 'agency_pan')}),
        ('Location info', {'fields': ('state', 'district', 'lat', 'long')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for the add page (when creating a new user in admin)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'full_name', 'contact', 'role', 'agency_pan', 'state', 'district',
                       'is_active', 'is_staff', 'is_superuser', 'is_verified'),
        }),
    )

    # As 'username' is None, we don't need to reference it in REQUIRED_FIELDS for admin
    # REQUIRED_FIELDS from the model are used for createsuperuser command.
    # UserAdmin handles the USERNAME_FIELD ('email' in your case) correctly.

    # If you have custom forms for user creation/change, specify them:
    # add_form_template = None
    # change_form_template = None

@admin.register(OTPStorage)
class OTPStorageAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'expires_at', 'created_at', 'is_expired')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('email',)
    readonly_fields = ('created_at', 'expires_at', 'is_expired')

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True # Display as a checkmark icon
    is_expired.short_description = 'Expired?'
