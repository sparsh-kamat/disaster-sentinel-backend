from django.urls import path
from .views import PastDisasterListView

urlpatterns = [
    path('api/past-disasters/', PastDisasterListView.as_view(), name='past_disasters_list'),
]

