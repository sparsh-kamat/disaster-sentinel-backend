from django.urls import path
from .views import PastDisasterListView
from .views import GdacsDisasterEventListView

urlpatterns = [
    path('api/past-disasters/', PastDisasterListView.as_view(), name='past_disasters_list'),
    path('api/disasters/', GdacsDisasterEventListView.as_view(), name='disaster-list'),
]

