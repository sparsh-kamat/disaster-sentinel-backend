from django.urls import path
from .views import StationList, StationListByState, FloodDetailsByGaugeID

urlpatterns = [
    path('stations/', StationList.as_view(), name='station-list'),
    path('stations/<str:state>/', StationListByState.as_view(), name='station-list-by-state'),
    path('flood-details/<int:gaugeid>/', FloodDetailsByGaugeID.as_view(), name='flood-details-by-gaugeid'),
]