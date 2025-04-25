# agency/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, ExistingAgenciesListView, VolunteerInterestViewSet, AgencyProfileViewSet, AgencyImageDeleteView
from .views import AgencyPermissionListView, AgencyMemberPermissionManageView

# Create a router and register the EventViewSet with it
router = DefaultRouter()
router.register(r'events', EventViewSet , basename='event')
router.register(r'volunteer-interests', VolunteerInterestViewSet, basename='volunteer-interest')
router.register(r'agency-profiles', AgencyProfileViewSet, basename='agencyprofile')


# Define the URL patterns for your agency app
urlpatterns = [
    path('existing-agencies/', ExistingAgenciesListView.as_view(), name='existing_agencies_list'),
    path('agency-images/<int:pk>/', AgencyImageDeleteView.as_view(), name='agency_image_delete'),
     # GET /api/agency/<agency_id>/permissions/
    path('agency/<int:agency_id>/permissions/',
         AgencyPermissionListView.as_view(),
         name='agency-permission-list'),

    # Manage permissions FOR a specific member UNDER an agency
    # GET, PUT, PATCH, DELETE /api/agency/<agency_id>/permissions/<member_id>/
    path('agency/<int:agency_id>/permissions/<int:member_id>/',
         AgencyMemberPermissionManageView.as_view(),
         name='agency-member-permission-manage'),

    path('', include(router.urls)),  # This will route '/events/'
    
]
