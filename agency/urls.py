# agency/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, ExistingAgenciesListView, VolunteerInterestViewSet


# Create a router and register the EventViewSet with it
router = DefaultRouter()
router.register(r'events', EventViewSet , basename='event')
router.register(r'volunteer-interests', VolunteerInterestViewSet, basename='volunteer-interest')

# Define the URL patterns for your agency app
urlpatterns = [
    path('existing-agencies/', ExistingAgenciesListView.as_view(), name='existing_agencies_list'),
    path('', include(router.urls)),  # This will route '/events/'
    
]
