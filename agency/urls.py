from django.urls import path
from rest_framework import routers, serializers, viewsets
from .models import ExistingAgencies
from .serializers import ExistingAgenciesSerializer
from .views import ExistingAgenciesListView



# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('api/agency/', ExistingAgenciesListView.as_view(), name='existing_agencies_list'),
]