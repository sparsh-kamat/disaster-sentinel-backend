from django.urls import path
from .views import DisasterSummaryAPIView
from .views import DisasterImagesAPIView
from .views import FloodPredictionAPIView  

urlpatterns = [
    path('api/disaster-summary/', DisasterSummaryAPIView.as_view(), name='disaster_summary'),
    path('api/disaster-images/' , DisasterImagesAPIView.as_view() , name = 'disaster_images'),
    path('api/predict/', FloodPredictionAPIView.as_view(), name='predict_flood'),
]