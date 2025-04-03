from django.urls import path, include
from rest_framework import routers, serializers, viewsets
from .models import ExistingAgencies
from .serializers import ExistingAgenciesSerializer
from .views import ExistingAgenciesListView
from rest_framework.routers import DefaultRouter

from .views import EventViewSet
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'events', EventViewSet)


# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('agency/', ExistingAgenciesListView.as_view(), name='existing_agencies_list'),
    path('', include(router.urls)),
    
]