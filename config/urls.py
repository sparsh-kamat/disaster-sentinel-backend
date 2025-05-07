from django.contrib import admin
from django.urls import path, include  # Import include
from .views import welcome_view  # Import the welcome_view

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin route
    path('', welcome_view, name='welcome'),  # This will map the root URL to the welcome view
    path('', include('users.urls')),  # Include URLs from the 'users' app (for signup, OTP verification, etc.)
    path('', include('past_disasters.urls')),  # Include URLs from the 'past_disasters' app (for the disaster API)
    path('api/', include('agency.urls')),  # Include URLs from the 'agency' app (for the agency API)
    path('', include('floodprediction.urls')),  # Include URLs from the 'floodprediction' app
    path('api/', include('floodstations.urls')),  # Include URLs from the 'floodstations' app
    path('api/', include('missingreport.urls')),  # Include URLs from the 'missingreport' app
    path('api/gdacs/', include('gdacs_api_app.urls')), # Include URLs from the 'gdacs_api_app' app (for the GDACS API)
]
