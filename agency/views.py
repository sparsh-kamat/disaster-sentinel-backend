from django.shortcuts import render
from .models import ExistingAgencies
from .serializers import ExistingAgenciesSerializer
from rest_framework import filters

from rest_framework import generics

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer
from django.contrib.auth import get_user_model

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        user_id = self.request.data.get('user_id')  # Get user_id from the request body
        user = get_user_model().objects.get(id=user_id)  # Get the user using user_id
        serializer.save(user=user)  # Associate the event with the user
        
    @action(detail=True, methods=['post'])
    def add_timeline(self, request, pk=None):
        event = self.get_object()
        timeline_items_data = request.data.get('timeline_items', [])
        for item_data in timeline_items_data:
            event.timeline_items.create(**item_data)
        return Response({'status': 'Timeline items added'})
    
    def get_queryset(self):
        """
        If 'user_id' is in the request, filter events by that user.
        Otherwise, return all events.
        """
        queryset = Event.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
class ExistingAgenciesListView(generics.ListAPIView):
    queryset = ExistingAgencies.objects.all()
    serializer_class = ExistingAgenciesSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = '__all__'  # Allow ordering by any field in the model

    def get_queryset(self):
        queryset = ExistingAgencies.objects.all()

        # Check if the 'state' parameter is in the request
        state = self.request.query_params.get('state', None)
        if state:
            # Filter disasters by state
            queryset = queryset.filter(state=state)
        
        return queryset
# This will render the 'welcome.html' template