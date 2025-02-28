from rest_framework import generics
from .models import PastDisaster
from .serializers import PastDisasterSerializer
from rest_framework import filters

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