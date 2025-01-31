from django.contrib import admin
from django.urls import path, include  # Import include

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin route
    path('auth/', include('users.urls')),  # Include URLs from the 'users' app (for signup, OTP verification, etc.)
    path('', include('past_disasters.urls')),  # Include URLs from the 'past_disasters' app (for the disaster API)
]
