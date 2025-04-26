from django.urls import path
from .views import PastDisasterListView
from .views import GdacsDisasterEventListView
from .views import GdacsDisasterEventTitleStateListView
urlpatterns = [
    path('api/past-disasters/', PastDisasterListView.as_view(), name='past_disasters_list'),
    path('api/disasters/', GdacsDisasterEventListView.as_view(), name='disaster-list'),
    path('disasters/title_state/', GdacsDisasterEventTitleStateListView.as_view(), name='disaster-title-state-list'),
]

