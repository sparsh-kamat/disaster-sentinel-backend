from rest_framework import generics
from .models import PastDisaster
from .serializers import PastDisasterSerializer
from rest_framework import filters

class PastDisasterListView(generics.ListAPIView):
    queryset = PastDisaster.objects.all()
    serializer_class = PastDisasterSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = '__all__'  # Allow ordering by any field in the model

    def get_queryset(self):
        queryset = PastDisaster.objects.all()

        # Check if the 'state' parameter is in the request
        state = self.request.query_params.get('state', None)
        if state:
            # Filter disasters by state
            queryset = queryset.filter(state=state)
        
        return queryset
