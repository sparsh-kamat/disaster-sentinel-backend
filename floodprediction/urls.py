from django.urls import path
from .views import DisasterSummaryAPIView

urlpatterns = [
    path('api/disaster-summary/', DisasterSummaryAPIView.as_view(), name='disaster_summary'),
]