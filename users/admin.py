from django.contrib import admin

# Register your models here.
# make it visible in admin panel
from .models import CustomUser

admin.site.register(CustomUser)
