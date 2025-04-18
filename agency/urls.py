# agency/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, ExistingAgenciesListView, VolunteerInterestViewSet, AgencyProfileViewSet, AgencyImageDeleteView


# Create a router and register the EventViewSet with it
router = DefaultRouter()
router.register(r'events', EventViewSet , basename='event')
router.register(r'volunteer-interests', VolunteerInterestViewSet, basename='volunteer-interest')
router.register(r'agency-profiles', AgencyProfileViewSet, basename='agencyprofile')


# Define the URL patterns for your agency app
urlpatterns = [
    path('existing-agencies/', ExistingAgenciesListView.as_view(), name='existing_agencies_list'),
    path('agency-images/<int:pk>/', AgencyImageDeleteView.as_view(), name='agency_image_delete'),
    path('', include(router.urls)),  # This will route '/events/'
    
]
