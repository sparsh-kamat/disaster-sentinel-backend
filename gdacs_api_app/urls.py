


# gdacs_api_app/urls.py 
# (Create this file in your app directory 'gdacs_api_app')

from django.urls import path
from .views import scrape_gdacs_view

urlpatterns = [
    # Defines the endpoint: /api/gdacs/scrape/?url=<GDACS_EVENT_URL>
    path('scrape/', scrape_gdacs_view, name='scrape_gdacs_event'),
]