from django.urls import path
from .views import DisasterSummaryAPIView
from .views import DisasterImagesAPIView
# from .views import FloodPredictionView

urlpatterns = [
    path('api/disaster-summary/', DisasterSummaryAPIView.as_view(), name='disaster_summary'),
    path('api/disaster-images/' , DisasterImagesAPIView.as_view() , name = 'disaster_images'),
    # path('api/flood-prediction/', FloodPredictionView.as_view(), name='flood_prediction'),
]