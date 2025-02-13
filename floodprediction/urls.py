from django.urls import path
from .views import DisasterSummaryAPIView

urlpatterns = [
    path('api/disaster-summary/', DisasterSummaryAPIView.as_view(), name='disaster_summary'),
    path('api/disaster-images/' , DisasterImagesAPIView.as_view() , name = 'disaster_images')
]