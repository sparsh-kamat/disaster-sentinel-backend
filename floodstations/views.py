from rest_framework import generics
from .models import StationInformation, FloodInformation
from .serializers import StationInformationSerializer, FloodInformationSerializer

# API 1: Fetch all stations
class StationList(generics.ListAPIView):
    queryset = StationInformation.objects.all()
    serializer_class = StationInformationSerializer

# API 2: Fetch stations by state filter
class StationListByState(generics.ListAPIView):
    serializer_class = StationInformationSerializer

    def get_queryset(self):
        state = self.kwargs['state']
        return StationInformation.objects.filter(state=state)

# API 3: Fetch flood details by gauge_id
class FloodDetailsByGaugeID(generics.ListAPIView):
    serializer_class = FloodInformationSerializer

    def get_queryset(self):
        gaugeid = self.kwargs['gaugeid']
        return FloodInformation.objects.filter(gaugeid=gaugeid)