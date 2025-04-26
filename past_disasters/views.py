from rest_framework import generics
from .models import PastDisaster
from .serializers import PastDisasterSerializer
from rest_framework import filters
from past_disasters.models import GdacsDisasterEvent
from .serializers import GdacsDisasterEventSerializer

class PastDisasterListView(generics.ListAPIView):
    queryset = PastDisaster.objects.all()
    serializer_class = PastDisasterSerializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = '__all__'  # Allow ordering by any field in the model
    search_fields = ['id']  # Add fields you want to search by

    def get_queryset(self):
        queryset = PastDisaster.objects.all()

        # Filter by state (if provided)
        state = self.request.query_params.get('state', None)
        if state:
            queryset = queryset.filter(state=state)

        # Search by disaster ID (if provided)
        disaster_id = self.request.query_params.get('id', None)
        if disaster_id:
            queryset = queryset.filter(id=disaster_id)

        return queryset
    


from django.db.models import F

class GdacsDisasterEventListView(generics.ListAPIView):
    serializer_class = GdacsDisasterEventSerializer

    def get_queryset(self):
        return GdacsDisasterEvent.objects.all().order_by(
            F('pubDate').desc(nulls_last=True),
            F('fromdate').desc(nulls_last=True)
        )

from .serializers import GdacsDisasterEventTitleStateSerializer

class GdacsDisasterEventTitleStateListView(generics.ListAPIView):
    queryset = GdacsDisasterEvent.objects.all()  # Or filter as needed
    serializer_class = GdacsDisasterEventTitleStateSerializer